from typing import List
from utils import fetch, clean_text, extract_location, extract_salary, is_remote, parse_date
from config import HIMALAYAS_QUERIES

API_URL = "https://himalayas.app/jobs/api/search"


def _normalize_item(item: dict) -> dict:
    # Try common keys used by job APIs; fall back to empty strings
    title = clean_text(item.get("title") or item.get(
        "position") or "", max_len=200)
    company = clean_text(
        (item.get("company") or {}).get("name") if isinstance(
            item.get("company"), dict) else item.get("company") or "",
        max_len=120,
    )
    # location may be a string or dict
    raw_loc = ""
    if isinstance(item.get("location"), dict):
        raw_loc = item.get("location").get("name") or ""
    else:
        raw_loc = item.get("location") or item.get(
            "city") or item.get("country") or ""
    description = clean_text(item.get("description")
                             or item.get("excerpt") or "", max_len=1200)
    url = item.get("url") or item.get(
        "apply_url") or item.get("canonical_url") or ""
    date_raw = item.get("published_at") or item.get(
        "created_at") or item.get("date") or ""

    return {
        "source": "Himalayas",
        "title": title,
        "company": company,
        "location": extract_location(raw_loc or description),
        "salary": extract_salary(description),
        "remote": is_remote(title + " " + description + " " + (raw_loc or "")),
        "description": description,
        "url": url,
        "date_posted": parse_date(date_raw),
    }


def scrape(queries: List[str] | None = None) -> List[dict]:
    """Query the Himalayas jobs API for each query and return normalized job dicts.
    If `queries` is None it uses `HIMALAYAS_QUERIES` from config.
    """
    queries = queries or HIMALAYAS_QUERIES
    all_jobs: List[dict] = []

    for q in queries:
        print(f"  → Himalayas query: {q}")
        params = {
            "q": q,
            "worldwide": "true",
            "seniority": "all",
        }
        resp = fetch(API_URL, timeout=15)
        # fetch wrapper doesn't pass params, so use requests directly if needed
        if resp is None:
            # fallback: try using requests with params (in case fetch was used incorrectly)
            try:
                import requests
                r = requests.get(API_URL, params=params, timeout=15)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print(f"    ✗ Request failed for query '{q}': {e}")
                continue
        else:
            try:
                # Note: some fetch wrappers return content only; use resp.json() safely
                data = resp.json()
            except Exception:
                try:
                    import json
                    data = json.loads(resp.content.decode(
                        'utf-8', errors='ignore'))
                except Exception as e:
                    print(f"    ✗ Failed to parse JSON for query '{q}': {e}")
                    continue

        # Himalayas API may return a list or an object with 'data' or 'results'
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # common wrappers
            items = data.get("data") or data.get(
                "results") or data.get("jobs") or []

        if not items:
            print(f"    ✓ 0 entries for '{q}'")
            continue

        for it in items:
            try:
                job = _normalize_item(it if isinstance(it, dict) else {})
                # Basic sanity: require a title and a URL or description
                if not job["title"]:
                    continue
                all_jobs.append(job)
            except Exception as e:
                print(f"    ✗ Failed to normalize item: {e}")
                continue

        print(f"    ✓ {len(items)} entries for '{q}'")

    return all_jobs
