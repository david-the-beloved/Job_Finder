# ─────────────────────────────────────────────────────────────
# scrapers/indeed.py  —  Indeed RSS feed scraper
# ─────────────────────────────────────────────────────────────
# Indeed exposes a free RSS feed for any search query.
# No API key needed. URL format:
#   https://www.indeed.com/rss?q=QUERY&l=LOCATION&sort=date
# ─────────────────────────────────────────────────────────────

import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from utils import fetch, clean_text, extract_salary, extract_location, is_remote, parse_date
from config import INDEED_SEARCHES


def _parse_feed(xml_bytes: bytes, query_label: str) -> list[dict]:
    jobs = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"    ✗ XML parse error: {e}")
        return jobs

    for item in root.findall(".//item"):
        def tag(name):
            el = item.find(name)
            return el.text.strip() if el is not None and el.text else ""

        title = tag("title")
        url = tag("link")
        description = clean_text(tag("description"), max_len=800)
        date_posted = parse_date(tag("pubDate"))

        # Indeed puts "company - location" in the title sometimes
        company = ""
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            title = parts[0].strip()
            company = parts[1].strip() if len(parts) > 1 else ""

        if not url:
            continue

        jobs.append({
            "source":      f"Indeed",
            "title":       title,
            "company":     company,
            "location":    extract_location(description),
            "salary":      extract_salary(description),
            "remote":      is_remote(title + " " + description),
            "description": description,
            "url":         url,
            "date_posted": date_posted,
        })

    return jobs


def scrape(searches: list[dict] = None) -> list[dict]:
    """
    Scrape Indeed RSS for every search in INDEED_SEARCHES.
    Returns a flat list of job dicts.
    """
    searches = searches or INDEED_SEARCHES
    all_jobs = []

    for search in searches:
        q = search.get("q", "")
        l = search.get("l", "")
        params = {"q": q, "l": l, "sort": "date", "limit": 50, "fromage": 7}
        url = f"https://www.indeed.com/rss?{urlencode(params)}"

        print(f"  → Indeed: '{q}' in '{l}'")
        resp = fetch(url)
        if resp is None:
            # If blocked (403), abort all remaining searches — they'll all fail too
            print(
                "  ✗ Indeed is blocking requests from this IP — skipping remaining searches")
            break

        jobs = _parse_feed(resp.content, f"{q}/{l}")
        print(f"    ✓ {len(jobs)} jobs found")
        all_jobs.extend(jobs)

    return all_jobs


if __name__ == "__main__":
    # Quick test — run this file directly
    import sys
    sys.path.insert(0, "..")
    jobs = scrape([{"q": "software engineer", "l": "remote"}])
    for j in jobs[:3]:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
    print(f"\nTotal: {len(jobs)}")
