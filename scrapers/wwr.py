import xml.etree.ElementTree as ET
from utils import fetch, clean_text, extract_location, extract_salary, is_remote, parse_date
from config import WWR_FEEDS

ATOM_NS = "http://www.w3.org/2005/Atom"


def _parse_feed(xml_bytes: bytes) -> list[dict]:
    jobs = []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"    ✗ XML parse error: {e}")
        return jobs

    # RSS items
    for item in root.findall(".//item"):
        title = clean_text(item.findtext("title") or "", max_len=200)
        link = (item.findtext("link") or "").strip()
        description = clean_text(item.findtext("description") or item.findtext(
            "content:encoded") or "", max_len=800)
        pub = item.findtext("pubDate") or item.findtext("published") or ""
        if not title or not link:
            continue
        jobs.append({
            "source": "WWR",
            "title": title,
            "company": "",
            "location": extract_location(description),
            "salary": extract_salary(description),
            "remote": is_remote(title + " " + description),
            "description": description,
            "url": link,
            "date_posted": parse_date(pub),
        })

    # Atom entries fallback
    for entry in root.findall(f"{{{ATOM_NS}}}entry"):
        def atom(tag):
            el = entry.find(f"{{{ATOM_NS}}}{tag}")
            return el.text.strip() if el is not None and el.text else ""
        title = clean_text(atom("title"), max_len=200)
        description = clean_text(
            atom("content") or atom("summary") or "", max_len=800)
        pub = atom("updated") or atom("published") or ""
        link_el = entry.find(f"{{{ATOM_NS}}}link")
        link = link_el.get("href", "") if link_el is not None else ""
        if not title or not link:
            continue
        jobs.append({
            "source": "WWR",
            "title": title,
            "company": "",
            "location": extract_location(description),
            "salary": extract_salary(description),
            "remote": is_remote(title + " " + description),
            "description": description,
            "url": link,
            "date_posted": parse_date(pub),
        })

    return jobs


def scrape(feeds: list[str] | None = None) -> list[dict]:
    feeds = feeds or WWR_FEEDS
    if not feeds:
        print("  ⚠ No WWR feed URLs configured — skipping")
        return []
    all_jobs = []
    for i, url in enumerate(feeds, 1):
        print(f"  → WWR feed {i}/{len(feeds)}")
        resp = fetch(url)
        if resp is None:
            continue
        jobs = _parse_feed(resp.content)
        print(f"    ✓ {len(jobs)} entries")
        all_jobs.extend(jobs)
    return all_jobs
