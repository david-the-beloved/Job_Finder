# ─────────────────────────────────────────────────────────────
# scrapers/google_alerts.py  —  Google Alerts RSS scraper
# ─────────────────────────────────────────────────────────────
# Setup:
#   1. Go to google.com/alerts
#   2. Create an alert (e.g. "software engineer" "now hiring")
#   3. Click ⚙ Show options → Deliver to: RSS feed
#   4. Click CREATE ALERT
#   5. Copy the RSS URL from the page → paste into config.py
#
# Good alert queries to create:
#   "software engineer" "we're hiring" 2026
#   "product manager" "job opening" remote
#   "data scientist" "full time" "apply now"
#   site:linkedin.com/jobs "senior developer"
#   "backend engineer" "now hiring" remote
# ─────────────────────────────────────────────────────────────

import xml.etree.ElementTree as ET
from utils import fetch, clean_text, extract_salary, extract_location, is_remote, parse_date
from config import GOOGLE_ALERT_FEEDS


ATOM_NS = "http://www.w3.org/2005/Atom"


def _parse_atom_feed(xml_bytes: bytes) -> list[dict]:
    """Parse an Atom RSS feed (format Google Alerts uses)."""
    jobs = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"    ✗ XML parse error: {e}")
        return jobs

    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        def atom(tag):
            el = entry.find(f"{{{ATOM_NS}}}{tag}")
            return el.text.strip() if el is not None and el.text else ""

        title       = clean_text(atom("title"), max_len=200)
        updated     = atom("updated")
        description = clean_text(atom("content") or atom("summary"), max_len=800)

        # Link is an attribute, not text content in Atom
        link_el = entry.find(f"{{{ATOM_NS}}}link")
        url = link_el.get("href", "") if link_el is not None else ""

        # Google Alerts wraps the real URL in a redirect — unwrap it
        if "google.com/url?q=" in url:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            params = urllib.parse.parse_qs(parsed.query)
            url = params.get("q", [url])[0]

        if not url or not title:
            continue

        jobs.append({
            "source":      "Google Alerts",
            "title":       title,
            "company":     "",   # usually not in alert title
            "location":    extract_location(description),
            "salary":      extract_salary(description),
            "remote":      is_remote(title + " " + description),
            "description": description,
            "url":         url,
            "date_posted": parse_date(updated),
        })

    return jobs


def scrape(feeds: list[str] = None) -> list[dict]:
    """
    Scrape all configured Google Alert RSS feeds.
    Returns a flat list of job dicts.
    """
    feeds    = feeds or GOOGLE_ALERT_FEEDS
    all_jobs = []

    if not feeds:
        print("  ⚠ No Google Alert URLs configured — skipping")
        print("    Add RSS URLs to GOOGLE_ALERT_FEEDS in config.py")
        return []

    for i, feed_url in enumerate(feeds, 1):
        print(f"  → Google Alert feed {i}/{len(feeds)}")
        resp = fetch(feed_url)
        if resp is None:
            continue

        jobs = _parse_atom_feed(resp.content)
        print(f"    ✓ {len(jobs)} entries")
        all_jobs.extend(jobs)

    return all_jobs


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    # Test with a sample public Atom feed to verify parser works
    print("Testing Google Alerts parser...")
    print("(Add URLs to config.py GOOGLE_ALERT_FEEDS to test with real alerts)")
