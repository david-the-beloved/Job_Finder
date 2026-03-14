# scrapers/remotive.py — Remotive public API scraper
# https://remotive.com/api/remote-jobs?category={category}&limit=100
# Free, no auth needed. Returns JSON.

import time
from utils import fetch, clean_text, parse_date, extract_salary
from config import REMOTIVE_CATEGORIES

API_URL = "https://remotive.com/api/remote-jobs"


def scrape(categories: list[str] | None = None) -> list[dict]:
    """
    Fetch Remotive jobs for each category.
    Returns a flat list of job dicts matching the shared schema.
    """
    categories = categories or REMOTIVE_CATEGORIES
    all_jobs = []
    seen_ids = set()

    for category in categories:
        url = f"{API_URL}?category={category}&limit=100"
        print(f"  → Remotive: '{category}'")

        resp = fetch(url)
        if resp is None:
            time.sleep(0.5)
            continue

        try:
            data = resp.json()
        except Exception as e:
            print(f"    ✗ JSON parse error: {e}")
            time.sleep(0.5)
            continue

        raw_jobs = data.get("jobs", [])
        count = 0

        for item in raw_jobs:
            job_id = str(item.get("id", ""))
            if job_id in seen_ids:
                continue
            seen_ids.add(job_id)

            url_link = item.get("url", "")
            if not url_link:
                continue

            description = clean_text(
                item.get("description", "") or "",
                max_len=800,
            )

            salary = (
                item.get("salary", "").strip()
                or extract_salary(description)
            )

            all_jobs.append({
                "source":      "Remotive",
                "title":       (item.get("title", "") or "")[:200],
                "company":     (item.get("company_name", "") or "")[:100],
                "location":    item.get("candidate_required_location", "Remote") or "Remote",
                "salary":      salary[:100] if salary else "",
                "remote":      "Yes",
                "description": description,
                "url":         url_link,
                "date_posted": parse_date(item.get("publication_date", "")),
            })
            count += 1

        print(f"    ✓ {count} jobs")
        time.sleep(0.5)

    return all_jobs


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    jobs = scrape(["software-dev"])
    for j in jobs[:3]:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
    print(f"\nTotal: {len(jobs)}")
