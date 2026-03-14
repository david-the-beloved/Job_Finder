#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# main.py  —  Run the full job scraper pipeline
# ─────────────────────────────────────────────────────────────
# Usage:
#   python main.py              # full run
#   python main.py --no-hn      # skip HackerNews (faster)
#   python main.py --excel-only # just rebuild Excel from DB
# ─────────────────────────────────────────────────────────────

import sys
import os
import time
from datetime import datetime

# Make sure all modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from database    import init_db, insert_job, log_run, get_stats
from export_excel import export
from utils       import passes_keyword_filter
from config      import HACKERNEWS_ENABLED

import scrapers.indeed        as indeed_scraper
import scrapers.remoteok      as remoteok_scraper
import scrapers.google_alerts as google_scraper
import scrapers.hackernews    as hn_scraper


def run_scraper(name: str, scrape_fn, *args) -> tuple[list, int]:
    """
    Run a single scraper, insert results into DB, return (jobs, new_count).
    Handles errors gracefully so one failed source doesn't kill the run.
    """
    print(f"\n{'─'*50}")
    print(f"📡 {name}")
    print(f"{'─'*50}")
    start = time.time()

    try:
        jobs = scrape_fn(*args) if args else scrape_fn()
    except Exception as e:
        print(f"  ✗ Scraper crashed: {e}")
        log_run(name, 0, 0, str(e))
        return [], 0

    new_count = 0
    skipped   = 0

    for job in jobs:
        # Keyword filter — skip irrelevant roles before storing
        if not passes_keyword_filter(job.get("title", "")):
            skipped += 1
            continue

        if insert_job(job):
            new_count += 1

    duration = time.time() - start
    print(f"  → Found: {len(jobs)}  |  New: {new_count}  |  "
          f"Filtered: {skipped}  |  Time: {duration:.1f}s")

    log_run(name, len(jobs), new_count)
    return jobs, new_count


def main():
    skip_hn      = "--no-hn"      in sys.argv
    excel_only   = "--excel-only" in sys.argv

    print("=" * 50)
    print("🔍 JOB SCRAPER")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # Initialise database
    print("\n🗄  Setting up database...")
    init_db()

    if excel_only:
        print("\n📊 Rebuilding Excel from database...")
        export()
        return

    total_new = 0

    # ── 1. Indeed RSS ──────────────────────────────────────────
    _, n = run_scraper("Indeed RSS", indeed_scraper.scrape)
    total_new += n

    # ── 2. RemoteOK API ────────────────────────────────────────
    _, n = run_scraper("RemoteOK API", remoteok_scraper.scrape)
    total_new += n

    # ── 3. Google Alerts RSS ───────────────────────────────────
    _, n = run_scraper("Google Alerts RSS", google_scraper.scrape)
    total_new += n

    # ── 4. HackerNews Who's Hiring ─────────────────────────────
    if HACKERNEWS_ENABLED and not skip_hn:
        _, n = run_scraper("HackerNews Who's Hiring", hn_scraper.scrape)
        total_new += n
    else:
        print("\n⏭  Skipping HackerNews")

    # ── 5. Export to Excel ─────────────────────────────────────
    print(f"\n{'─'*50}")
    print("📊 Exporting to Excel...")
    print(f"{'─'*50}")
    export()

    # ── Summary ────────────────────────────────────────────────
    stats = get_stats()
    print(f"""
{'='*50}
✅ RUN COMPLETE
{'='*50}
  New jobs this run : {total_new}
  Total in database : {stats['total']}
  Remote jobs       : {stats['remote']}
  Finished          : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*50}
""")


if __name__ == "__main__":
    main()
