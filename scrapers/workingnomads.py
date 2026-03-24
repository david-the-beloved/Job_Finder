import requests
from utils import clean_text, extract_location, extract_salary, is_remote, parse_date

API_URL = "https://www.workingnomads.co/api/exposed_jobs/"


def _normalize(item: dict) -> dict:
    title = clean_text(item.get("title") or "", max_len=200)
    company = clean_text(item.get("company") or item.get(
        "company_name") or "", max_len=120)
    description = clean_text(item.get("description")
                             or item.get("content") or "", max_len=1200)
    url = item.get("url") or item.get("apply_url") or item.get("link") or ""
    pub = item.get("date") or item.get(
        "created_at") or item.get("published") or ""
    return {
        "source": "Working Nomads",
        "title": title,
        "company": company,
        "location": extract_location(item.get("location") or description),
        "salary": extract_salary(description),
        "remote": is_remote(title + " " + description),
        "description": description,
        "url": url,
        "date_posted": parse_date(pub),
    }


def scrape() -> list[dict]:
    print("  → Working Nomads API")
    all_jobs = []
    try:
        r = requests.get(API_URL, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"    ✗ Failed to fetch Working Nomads API: {e}")
        return []

    # data is expected to be a list of job dicts
    items = data if isinstance(data, list) else data.get(
        "jobs") or data.get("data") or []
    for it in items:
        try:
            # filter by category_name or tags if available - keep all for now
            job = _normalize(it if isinstance(it, dict) else {})
            if not job["title"]:
                continue
            all_jobs.append(job)
        except Exception as e:
            print(f"    ✗ Normalize failed: {e}")
            continue

    print(f"    ✓ {len(all_jobs)} entries")
    return all_jobs
