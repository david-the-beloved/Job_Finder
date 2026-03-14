#!/usr/bin/env python3
# ──────────────────────────────────────────────────────────────
# main.py -- Full pipeline: scrape -> verify -> export
# ──────────────────────────────────────────────────────────────
# Usage:
#   python main.py               # full run (scrape + verify + export)
#   python main.py --no-hn       # skip HackerNews (faster daily runs)
#   python main.py --no-verify   # skip AI verification (scrape only)
#   python main.py --verify-only # run AI on existing unverified jobs
#   python main.py --excel-only  # just rebuild Excel from DB
# ──────────────────────────────────────────────────────────────

import scrapers.hackernews as hn_scraper
import scrapers.google_alerts as google_scraper
import scrapers.remoteok as remoteok_scraper
import scrapers.remotive as remotive_scraper
import scrapers.indeed as indeed_scraper
from config import HACKERNEWS_ENABLED, GEMINI_API_KEY, GOOGLE_SHEETS_ENABLED, GOOGLE_SHEET_ID
from verify import verify_batch, get_quota_status
from utils import passes_keyword_filter
from export_excel import export
from database import init_db, insert_job, log_run, get_stats
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))


def run_scraper(name: str, scrape_fn, *args) -> tuple[list, int]:
    print(f"\n{'─'*52}")
    print(f"  {name}")
    print(f"{'─'*52}")
    start = time.time()
    try:
        jobs = scrape_fn(*args) if args else scrape_fn()
    except Exception as e:
        print(f"  Scraper crashed: {e}")
        log_run(name, 0, 0, str(e))
        return [], 0

    new_count = 0
    skipped = 0
    for job in jobs:
        if not passes_keyword_filter(job.get("title", "")):
            skipped += 1
            continue
        if insert_job(job):
            new_count += 1

    duration = time.time() - start
    print(
        f"  Found: {len(jobs)}  |  New: {new_count}  |  Filtered: {skipped}  |  {duration:.1f}s")
    log_run(name, len(jobs), new_count)
    return jobs, new_count


def main():
    args = sys.argv[1:]
    skip_hn = "--no-hn" in args
    skip_verify = "--no-verify" in args
    verify_only = "--verify-only" in args
    excel_only = "--excel-only" in args

    print("\n" + "=" * 52)
    print("  JOB SCRAPER")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 52)

    init_db()

    # ── Excel only ─────────────────────────────────────────────
    if excel_only:
        print("\n  Rebuilding Excel from database...")
        export()

        if GOOGLE_SHEETS_ENABLED and GOOGLE_SHEET_ID:
            from export_sheets import export_to_sheets
            export_to_sheets()

        from export_csv import export_csv
        export_csv()
        return

    total_new = 0

    # ── Scraping phase ─────────────────────────────────────────
    if not verify_only:
        _, n = run_scraper("Indeed RSS",        indeed_scraper.scrape)
        total_new += n

        _, n = run_scraper("RemoteOK API",      remoteok_scraper.scrape)
        total_new += n

        _, n = run_scraper("Remotive API",       remotive_scraper.scrape)
        total_new += n

        _, n = run_scraper("Google Alerts RSS", google_scraper.scrape)
        total_new += n

        if HACKERNEWS_ENABLED and not skip_hn:
            _, n = run_scraper("HackerNews Who's Hiring", hn_scraper.scrape)
            total_new += n
        else:
            print("\n  Skipping HackerNews (--no-hn or disabled in config)")

    # ── AI verification phase ──────────────────────────────────
    if not skip_verify and GEMINI_API_KEY:
        print(f"\n{'─'*52}")
        print("  AI VERIFICATION (Gemini)")
        print(f"{'─'*52}")

        quota = get_quota_status()
        print(f"  Free calls remaining: {quota['free_remaining']}/{20}")
        if quota["is_on_paid"]:
            print(
                f"  Note: On paid tier today (${quota['cost_usd']:.4f} spent)")

        verify_batch()

    elif not skip_verify and not GEMINI_API_KEY:
        print("\n  Skipping AI verification -- no GEMINI_API_KEY set")
        print("  Add your key to config.py to enable verification")

    # ── Excel export ───────────────────────────────────────────
    print(f"\n{'─'*52}")
    print("  EXCEL EXPORT")
    print(f"{'─'*52}")
    export()

    if GOOGLE_SHEETS_ENABLED and GOOGLE_SHEET_ID:
        from export_sheets import export_to_sheets
        export_to_sheets()

    from export_csv import export_csv
    export_csv()

    # ── Final summary ──────────────────────────────────────────
    stats = get_stats()
    print(f"""
{'='*52}
  DONE
  New jobs this run : {total_new}
  Total in database : {stats['total']}
  Remote jobs       : {stats['remote']}
  Finished          : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*52}
""")


if __name__ == "__main__":
    main()
