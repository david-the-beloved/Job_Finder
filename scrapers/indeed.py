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


def scrape(searches: list[dict] | None = None) -> list[dict]:
    print("  ⚠ Indeed scraper disabled (blocks server IPs)")
    return []


if __name__ == "__main__":
    # Quick test — run this file directly
    import sys
    sys.path.insert(0, "..")
    jobs = scrape([{"q": "software engineer", "l": "remote"}])
    for j in jobs[:3]:
        print(f"  {j['title']} @ {j['company']} — {j['location']}")
    print(f"\nTotal: {len(jobs)}")
