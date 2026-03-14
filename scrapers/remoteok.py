# ─────────────────────────────────────────────────────────────
# scrapers/remoteok.py  —  RemoteOK public JSON API scraper
# ─────────────────────────────────────────────────────────────
# RemoteOK exposes a free public API at remoteok.com/api
# No auth needed. Returns JSON array of job objects.
# Rate limit: be respectful — one call per run is fine.
# ─────────────────────────────────────────────────────────────

from utils import fetch, clean_text, extract_salary, parse_date
from config import REMOTEOK_TAGS


API_URL = "https://remoteok.com/api"


def _format_salary(job: dict) -> str:
    lo = job.get("salary_min")
    hi = job.get("salary_max")
    if lo and hi:
        return f"${int(lo):,} - ${int(hi):,}"
    if lo:
        return f"${int(lo):,}+"
    return ""


def scrape(tags: list[str] = None) -> list[dict]:
    """
    Fetch RemoteOK jobs, optionally filtered by tag.
    Returns a list of job dicts.
    """
    tags = tags or REMOTEOK_TAGS
    print("  → RemoteOK API")

    resp = fetch(API_URL)
    if resp is None:
        return []

    try:
        data = resp.json()
    except Exception as e:
        print(f"    ✗ JSON parse error: {e}")
        return []

    # First element is a legal notice, skip it
    raw_jobs = [j for j in data[1:] if isinstance(j, dict)]

    jobs = []
    for item in raw_jobs:
        # Tag filter
        job_tags = [t.lower() for t in item.get("tags", [])]
        if tags and not any(t.lower() in job_tags for t in tags):
            continue

        description = clean_text(
            item.get("description", "") or item.get("text", ""),
            max_len=800
        )

        url = item.get("url", "") or item.get("apply_url", "")
        if not url:
            slug = item.get("slug", "")
            url  = f"https://remoteok.com/remote-jobs/{slug}" if slug else ""

        if not url:
            continue

        jobs.append({
            "source":      "RemoteOK",
            "title":       item.get("position", "")[:200],
            "company":     item.get("company", "")[:100],
            "location":    "Remote",
            "salary":      _format_salary(item),
            "remote":      "Yes",
            "description": description,
            "url":         url,
            "date_posted": parse_date(item.get("date", "")),
        })

    print(f"    ✓ {len(jobs)} jobs (filtered from {len(raw_jobs)} total)")
    return jobs


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    jobs = scrape(["python", "react"])
    for j in jobs[:3]:
        print(f"  {j['title']} @ {j['company']} — {j['salary']}")
    print(f"\nTotal: {len(jobs)}")
