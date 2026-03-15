#!/usr/bin/env python3
# verify.py -- Gemini AI verification layer

import json
import os
import time
import requests
from datetime import datetime, date

from config import (
    GEMINI_API_KEY, GEMINI_MODEL, GEMINI_FREE_RPD,
    GEMINI_MAX_CALLS_PER_RUN, GEMINI_QUOTA_FILE, MIN_QUALITY_SCORE
)
from database import get_connection, init_db


GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent?key={key}"
)

SYSTEM_PROMPT = """You are a job posting analyst. Analyse the job posting and return ONLY a valid JSON object — no markdown, no explanation, just the JSON.

Return this exact structure:
{
  "verified": true,
  "scam_flag": "",
  "company": "Company Name",
  "location": "City, State or Remote",
  "salary": "$X - $Y",
  "remote": "Yes",
  "tech_stack": ["Python", "React"],
  "quality_score": 8,
  "quality_reason": "Clear requirements, reputable company, competitive salary"
}

Rules:
- verified: true if this appears to be a real, legitimate job posting
- scam_flag: empty string if clean, otherwise a SHORT reason (e.g. "Vague company, no requirements, unrealistic pay")
- company: extract or improve the company name
- location: "Remote", "Hybrid - City", or "City, State/Country"
- salary: extract salary range if present, else empty string
- remote: "Yes", "Hybrid", or "No"
- tech_stack: list of specific technologies/tools mentioned (max 8). Empty list if none.
- quality_score: 1-10 integer. Score based on:
    10: Clear role, reputable company, salary listed, specific requirements, apply link works
    7-9: Most info present, legitimate looking
    4-6: Some info missing but seems real
    2-3: Vague, recruiter spam, or missing most details
    1: Scam, fake, or completely useless posting
- quality_reason: one sentence explaining the score"""


def _readable_date(dt: datetime = None) -> str:
    """Return a human-readable date string e.g. March 14, 2026 at 08:00."""
    dt = dt or datetime.now()
    return dt.strftime("%B %d, %Y at %H:%M")


def _call_gemini(prompt: str) -> dict | None:
    """
    Make a single Gemini API call.
    Returns parsed JSON dict, or None if quota exceeded / any error.
    Does NOT retry on 429 -- just returns None and lets the loop continue.
    """
    url = GEMINI_URL.format(model=GEMINI_MODEL, key=GEMINI_API_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 400,
        },
    }

    try:
        resp = requests.post(url, json=payload, timeout=20)

        # Quota exceeded -- silently skip, do not retry, do not wait
        if resp.status_code == 429:
            return None

        # Bad API key
        if resp.status_code == 403:
            print("    ERROR: Invalid API key. Check GEMINI_API_KEY in config.py")
            return None

        resp.raise_for_status()
        data = resp.json()

        text = (data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", ""))

        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        return json.loads(text)

    except json.JSONDecodeError:
        return None
    except Exception:
        return None


# ── Quota Tracker ─────────────────────────────────────────────

def _load_quota() -> dict:
    today = str(date.today())
    if os.path.exists(GEMINI_QUOTA_FILE):
        try:
            with open(GEMINI_QUOTA_FILE) as f:
                data = json.load(f)
            if data.get("date") == today:
                return data
        except Exception:
            pass
    return {"date": today, "calls": 0, "paid_calls": 0, "cost_usd": 0.0}


def _save_quota(quota: dict):
    os.makedirs(os.path.dirname(GEMINI_QUOTA_FILE), exist_ok=True)
    with open(GEMINI_QUOTA_FILE, "w") as f:
        json.dump(quota, f, indent=2)


def get_quota_status() -> dict:
    quota = _load_quota()
    free_remaining = max(0, GEMINI_FREE_RPD - quota["calls"])
    return {
        "calls_today":    quota["calls"],
        "free_remaining": free_remaining,
        "paid_calls":     quota.get("paid_calls", 0),
        "cost_usd":       quota.get("cost_usd", 0.0),
        "is_on_paid":     quota["calls"] >= GEMINI_FREE_RPD,
    }


# ── DB Helpers ────────────────────────────────────────────────

def get_unverified_jobs(limit: int = None) -> list:
    conn = get_connection()
    query = """
        SELECT id, title, company, location, description, url, source
        FROM jobs
        WHERE verified IS NULL
        ORDER BY date_found DESC
    """
    if limit:
        query += f" LIMIT {limit}"
    rows = [dict(r) for r in conn.execute(query).fetchall()]
    conn.close()
    return rows


def _update_job_ai_fields(job_id: str, ai: dict):
    conn = get_connection()
    tech_stack = ", ".join(ai.get("tech_stack", []))
    conn.execute("""
        UPDATE jobs SET
            verified      = ?,
            scam_flag     = ?,
            quality_score = ?,
            tech_stack    = ?,
            company       = CASE WHEN ? != '' THEN ? ELSE company END,
            location      = CASE WHEN ? != '' THEN ? ELSE location END,
            salary        = CASE WHEN ? != '' THEN ? ELSE salary END,
            remote        = CASE WHEN ? != '' THEN ? ELSE remote END,
            last_checked  = ?
        WHERE id = ?
    """, (
        1 if ai.get("verified") else 0,
        ai.get("scam_flag", ""),
        ai.get("quality_score", 5),
        tech_stack,
        ai.get("company", ""),  ai.get("company", ""),
        ai.get("location", ""), ai.get("location", ""),
        ai.get("salary", ""),   ai.get("salary", ""),
        ai.get("remote", ""),   ai.get("remote", ""),
        _readable_date(),       # human-readable last_checked
        job_id,
    ))
    conn.commit()
    conn.close()


# ── Main Verification Runner ──────────────────────────────────

def verify_batch(max_calls: int = None) -> dict:
    if not GEMINI_API_KEY:
        print("  !! GEMINI_API_KEY not set -- skipping AI verification")
        print("     Add your key to config.py")
        print("     Get a free key at: aistudio.google.com/app/apikey")
        return {"skipped": True}

    max_calls = max_calls or GEMINI_MAX_CALLS_PER_RUN
    quota = _load_quota()
    status = get_quota_status()
    unverified = get_unverified_jobs(limit=max_calls)

    if not unverified:
        print("  -- No unverified jobs to process")
        return {"verified": 0, "scams": 0, "errors": 0, "skipped_quota": 0}

    print(f"  Jobs to verify   : {len(unverified)}")
    print(f"  Free calls left  : {status['free_remaining']}/{GEMINI_FREE_RPD}")
    if status["is_on_paid"]:
        print(
            f"  Mode             : PAID (${status['cost_usd']:.4f} spent today)")
    else:
        print(f"  Mode             : FREE tier")
    print()

    verified_count = 0
    scam_count = 0
    error_count = 0
    skipped_quota = 0
    calls_this_run = 0

    for i, job in enumerate(unverified):

        prompt = f"""{SYSTEM_PROMPT}

---JOB POSTING---
Title:       {job.get('title', '')}
Company:     {job.get('company', '')}
Location:    {job.get('location', '')}
Source:      {job.get('source', '')}
URL:         {job.get('url', '')}
Description: {job.get('description', '')[:600]}
"""

        print(f"  [{i+1}/{len(unverified)}] {job['title'][:50]:<50}",
              end=" ", flush=True)

        ai_result = _call_gemini(prompt)

        if ai_result is None:
            # Could be quota exceeded or any other error.
            # Silently skip -- do not mark the job, retry next run.
            skipped_quota += 1
            print("SKIPPED")
        else:
            _update_job_ai_fields(job["id"], ai_result)
            score = ai_result.get("quality_score", 0)
            is_scam = bool(ai_result.get("scam_flag", ""))

            if is_scam:
                scam_count += 1
                print(
                    f"SCAM  (score:{score}) {ai_result.get('scam_flag', '')[:40]}")
            else:
                print(
                    f"OK    (score:{score}) {ai_result.get('quality_reason', '')[:40]}")

            verified_count += 1
            calls_this_run += 1

            # Update quota tracking
            quota["calls"] += 1
            if quota["calls"] > GEMINI_FREE_RPD:
                quota["paid_calls"] = quota.get("paid_calls", 0) + 1
                quota["cost_usd"] = quota.get("cost_usd", 0.0) + 0.000098
            _save_quota(quota)

        # Respectful delay between calls
        time.sleep(0.5)

    final_quota = _load_quota()
    print(f"""
  Verification Summary
  ────────────────────────────────────────
  Processed    : {calls_this_run}
  Verified OK  : {verified_count}
  Scams found  : {scam_count}
  Skipped      : {skipped_quota} (quota or error -- will retry next run)
  API calls today : {final_quota['calls']} (free limit: {GEMINI_FREE_RPD})
  Est. cost today : ${final_quota.get('cost_usd', 0):.4f}
  Run completed   : {_readable_date()}
  ────────────────────────────────────────""")

    return {
        "verified":      verified_count,
        "scams":         scam_count,
        "errors":        error_count,
        "skipped_quota": skipped_quota,
        "api_calls":     calls_this_run,
        "cost_today":    final_quota.get("cost_usd", 0.0),
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    init_db()
    print("=" * 50)
    print("AI VERIFICATION -- Running standalone")
    print("=" * 50)
    result = verify_batch()
    if not result.get("skipped"):
        print(
            f"\nDone. Verified {result['verified']} jobs, caught {result['scams']} scams.")
