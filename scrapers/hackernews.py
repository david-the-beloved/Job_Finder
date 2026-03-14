# ─────────────────────────────────────────────────────────────
# scrapers/hackernews.py  —  HN "Who's Hiring" thread scraper
# ─────────────────────────────────────────────────────────────
# Every first Monday of the month, HN posts a "Who's Hiring"
# thread with hundreds of direct postings from real companies,
# no recruiters. This scraper finds the latest thread and
# pulls every top-level comment as a job posting.
#
# HN Algolia API docs: hn.algolia.com/api
# ─────────────────────────────────────────────────────────────

import requests
from utils import clean_text, extract_salary, extract_location, is_remote, parse_date


HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
HN_ITEM_URL   = "https://hacker-news.firebaseio.com/v0/item/{}.json"


def _get_latest_whos_hiring_id() -> int | None:
    """Find the most recent 'Ask HN: Who is hiring?' thread."""
    params = {
        "query":     "Ask HN: Who is hiring?",
        "tags":      "story,ask_hn",
        "hitsPerPage": 5,
    }
    try:
        resp = requests.get(HN_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        if hits:
            return int(hits[0]["objectID"])
    except Exception as e:
        print(f"    ✗ Could not find HN hiring thread: {e}")
    return None


def _get_comments(story_id: int) -> list[dict]:
    """Fetch top-level comments (individual job posts) from the thread."""
    try:
        resp = requests.get(HN_ITEM_URL.format(story_id), timeout=10)
        story = resp.json()
        return story.get("kids", [])[:200]  # cap at 200 comments
    except Exception as e:
        print(f"    ✗ Could not fetch HN thread: {e}")
        return []


def _parse_comment(comment_id: int, thread_date: str) -> dict | None:
    """Turn a HN comment into a job dict."""
    try:
        resp = requests.get(HN_ITEM_URL.format(comment_id), timeout=10)
        item = resp.json()
    except Exception:
        return None

    if item.get("dead") or item.get("deleted"):
        return None

    raw_text = item.get("text", "")
    if not raw_text or len(raw_text) < 50:
        return None

    text_clean = clean_text(raw_text, max_len=1000)

    # First line is usually "Company | Role | Location | Remote"
    first_line = text_clean.split("\n")[0][:200]
    parts      = [p.strip() for p in first_line.split("|")]

    company  = parts[0] if len(parts) > 0 else ""
    title    = parts[1] if len(parts) > 1 else "Software Engineer"
    location = parts[2] if len(parts) > 2 else extract_location(text_clean)

    url = f"https://news.ycombinator.com/item?id={comment_id}"

    return {
        "source":      "HackerNews Who's Hiring",
        "title":       title[:200],
        "company":     company[:100],
        "location":    location[:100] or extract_location(text_clean),
        "salary":      extract_salary(text_clean),
        "remote":      is_remote(first_line + " " + text_clean),
        "description": text_clean,
        "url":         url,
        "date_posted": thread_date,
    }


def scrape() -> list[dict]:
    """
    Scrape the latest HN Who's Hiring thread.
    Returns a list of job dicts.
    NOTE: Makes many small HTTP requests — can take 1-2 minutes.
    """
    print("  → Hacker News: Who's Hiring")

    story_id = _get_latest_whos_hiring_id()
    if not story_id:
        return []

    print(f"    Found thread ID: {story_id}")
    comment_ids = _get_comments(story_id)
    print(f"    Fetching {len(comment_ids)} comments...")

    # Get thread date
    try:
        resp        = requests.get(HN_ITEM_URL.format(story_id), timeout=10)
        thread_time = resp.json().get("time", 0)
        from datetime import datetime
        thread_date = datetime.fromtimestamp(thread_time).strftime("%Y-%m-%d")
    except Exception:
        thread_date = ""

    jobs = []
    for i, cid in enumerate(comment_ids):
        job = _parse_comment(cid, thread_date)
        if job:
            jobs.append(job)
        # Progress every 25 comments
        if (i + 1) % 25 == 0:
            print(f"    ... {i+1}/{len(comment_ids)}")

    print(f"    ✓ {len(jobs)} jobs parsed from HN thread")
    return jobs


if __name__ == "__main__":
    import sys
    sys.path.insert(0, "..")
    jobs = scrape()
    for j in jobs[:3]:
        print(f"  {j['title']} @ {j['company']} — {j['remote']}")
    print(f"\nTotal: {len(jobs)}")
