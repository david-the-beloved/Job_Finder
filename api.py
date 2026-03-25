# api.py -- FastAPI HTTP endpoint for n8n to fetch jobs
from config import MIN_QUALITY_SCORE, CATEGORY_RULES
from database import get_connection, init_db
import io
import contextlib
from datetime import datetime, timedelta
from fastapi import FastAPI, BackgroundTasks, HTTPException, Header
import re
from fastapi.responses import JSONResponse
import uvicorn
import sys
import os
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


app = FastAPI(title="Job Scraper API")

with contextlib.redirect_stdout(io.StringIO()):
    init_db()


@app.get("/jobs/unsynced")
def get_unsynced_jobs_api(limit: int = 500, min_quality: int = 1):
    """
    Returns jobs not yet synced to Google Sheets (synced_to_sheets = 0).
    Use this from n8n to fetch only new jobs to append to sheets.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, source, title, company, location, salary, remote,
               tech_stack, quality_score, date_posted, date_found,
               url, verified, scam_flag, description
        FROM jobs
        WHERE (synced_to_sheets IS NULL OR synced_to_sheets = 0)
          AND (scam_flag IS NULL OR scam_flag = '')
          AND (quality_score IS NULL OR quality_score >= ?)
        ORDER BY date_found DESC
        LIMIT ?
    """, (min_quality, limit)).fetchall()
    conn.close()

    jobs = []
    for r in rows:
        # Check title, tech stack, and description for much better accuracy
        category = _categorise(f"{r[2] or ''} {r[7] or ''} {r[14] or ''}")

        jobs.append({
            "ID":          r[0] or "",
            "Source":      r[1] or "",
            "Title":       r[2] or "",
            "Company":     r[3] or "",
            "Location":    r[4] or "",
            "Salary":      r[5] or "",
            "Remote":      r[6] or "",
            "Tech Stack":  r[7] or "",
            "Score":       r[8] if r[8] is not None else "",
            "Date Posted": _fmt_date(r[9] or ""),
            "Date Found":  _fmt_date(r[10] or ""),
            "URL":         r[11] or "",
            "Verified":    _fmt_verified(r[12]),
            "Description": (r[14] or "")[:300],
            "Category":    category,
        })

    return JSONResponse(content=jobs)


@app.post("/jobs/mark_synced")
def mark_jobs_synced(body: list[str]):
    """
    Mark a list of job IDs as synced to Google Sheets.
    Example POST body: ["id1", "id2"]
    """
    if not isinstance(body, list):
        return JSONResponse(status_code=400, content={"error": "Expected list of job IDs"})
    conn = get_connection()
    conn.executemany("UPDATE jobs SET synced_to_sheets = 1 WHERE id = ?", [
                     (i,) for i in body])
    conn.commit()
    conn.close()
    return JSONResponse(content={"updated": len(body)})


def _categorise(text_to_check: str) -> str:
    """
    Categorise by checking keywords against a combined text string.
    Safely handles special characters like C++ or UI/UX.
    """
    t = (text_to_check or "").lower()

    for category, keywords in CATEGORY_RULES:
        for k in keywords:
            k_norm = (k or "").lower().strip()
            if not k_norm:
                continue

            # If keyword contains special characters at the edges, drop the \b constraint for that edge
            pattern = re.escape(k_norm)

            # Only apply word boundary if the keyword starts with an alphanumeric character
            if k_norm[0].isalnum():
                pattern = r"\b" + pattern
            # Only apply word boundary if the keyword ends with an alphanumeric character
            if k_norm[-1].isalnum():
                pattern = pattern + r"\b"

            if re.search(pattern, t, flags=re.IGNORECASE):
                return category

    return "Other"


def _fmt_date(raw: str) -> str:
    if not raw:
        return ""
    for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d"]:
        try:
            return datetime.strptime(raw[:16], fmt).strftime("%B %d, %Y")
        except ValueError:
            continue
    return raw[:10]


def _fmt_verified(val) -> str:
    if val == 1:
        return "Yes"
    if val == 0:
        return "No"
    return "Pending"


# ── Routes ────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "time": datetime.now().strftime("%Y-%m-%d %H:%M")}


# ── Manual Trigger Route ──────────────────────────────────────

def execute_scraper_script():
    """The actual function that runs in the background"""
    print("Manual scraper run triggered via API...")
    subprocess.run(["python", "main.py", "--no-hn", "--no-verify"])
    print("Manual scraper run complete.")


@app.post("/run-scraper")
def trigger_manual_scrape(background_tasks: BackgroundTasks, secret_key: str = Header(None)):
    """
    Endpoint to manually trigger the scraper. 
    Requires a secret header so random people on the internet don't burn your AI credits!
    """
    # Change 'my-super-secret-password' to whatever you want
    if secret_key != "skillboost":
        raise HTTPException(
            status_code=401, detail="Unauthorized. Nice try though!")

    # This tells FastAPI to return a success message instantly,
    # but run the heavy scraping script in the background.
    background_tasks.add_task(execute_scraper_script)

    return {"status": "success", "message": "Scraper started in the background. Check Railway logs for progress."}


@app.get("/jobs")
def get_jobs(hours: int = 24, limit: int = 500):
    """
    Returns clean jobs from the last N hours.
    Query params:
      hours = how many hours back to fetch (default 24)
      limit = max jobs to return (default 500)
    """
    cutoff = (datetime.now() - timedelta(hours=hours)
              ).strftime("%Y-%m-%d %H:%M")
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, source, title, company, location, salary, remote,
               tech_stack, quality_score, date_posted, date_found,
               url, verified, scam_flag, description
        FROM jobs
        WHERE date_found >= ?
          AND (scam_flag IS NULL OR scam_flag = '')
          AND (quality_score IS NULL OR quality_score >= ?)
          AND (still_active IS NULL OR still_active = 1)
        ORDER BY quality_score DESC, date_found DESC
        LIMIT ?
    """, (cutoff, MIN_QUALITY_SCORE, limit)).fetchall()
    conn.close()

    jobs = []
    for r in rows:
        jobs.append({
            "ID":          r[0] or "",
            "Source":      r[1] or "",
            "Title":       r[2] or "",
            "Company":     r[3] or "",
            "Location":    r[4] or "",
            "Salary":      r[5] or "",
            "Remote":      r[6] or "",
            "Tech Stack":  r[7] or "",
            "Score":       r[8] if r[8] is not None else "",
            "Date Posted": _fmt_date(r[9] or ""),
            "Date Found":  _fmt_date(r[10] or ""),
            "URL":         r[11] or "",
            "Verified":    _fmt_verified(r[12]),
            "Description": (r[14] or "")[:300],
            "Category":    _categorise(f"{r[2] or ''} {r[7] or ''} {r[14] or ''}"),
        })

    return JSONResponse(content=jobs)


@app.get("/jobs/all")
def get_all_jobs(limit: int = 1000):
    """
    Returns ALL jobs regardless of date.
    Use for full sync or manual resets.
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, source, title, company, location, salary, remote,
               tech_stack, quality_score, date_posted, date_found,
               url, verified, scam_flag, description
        FROM jobs
        WHERE (scam_flag IS NULL OR scam_flag = '')
          AND (quality_score IS NULL OR quality_score >= ?)
          AND (still_active IS NULL OR still_active = 1)
        ORDER BY quality_score DESC, date_found DESC
        LIMIT ?
    """, (MIN_QUALITY_SCORE, limit)).fetchall()
    conn.close()

    jobs = []
    for r in rows:
        jobs.append({
            "ID":          r[0] or "",
            "Source":      r[1] or "",
            "Title":       r[2] or "",
            "Company":     r[3] or "",
            "Location":    r[4] or "",
            "Salary":      r[5] or "",
            "Remote":      r[6] or "",
            "Tech Stack":  r[7] or "",
            "Score":       r[8] if r[8] is not None else "",
            "Date Posted": _fmt_date(r[9] or ""),
            "Date Found":  _fmt_date(r[10] or ""),
            "URL":         r[11] or "",
            "Verified":    _fmt_verified(r[12]),
            "Description": (r[14] or "")[:300],
            "Category":    _categorise(f"{r[2] or ''} {r[7] or ''} {r[14] or ''}"),
        })

    return JSONResponse(content=jobs)


@app.get("/stats")
def get_stats():
    """Returns database stats."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    remote = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE remote='Yes'").fetchone()[0]
    verified = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE verified=1").fetchone()[0]
    unverified = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE verified IS NULL").fetchone()[0]
    scams = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE scam_flag != '' AND scam_flag IS NOT NULL").fetchone()[0]
    today = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE date_found LIKE ?",
        (datetime.now().strftime("%Y-%m-%d") + "%",)
    ).fetchone()[0]
    sources = dict(conn.execute(
        "SELECT source, COUNT(*) FROM jobs GROUP BY source ORDER BY COUNT(*) DESC"
    ).fetchall())
    conn.close()

    return {
        "total":      total,
        "today":      today,
        "remote":     remote,
        "verified":   verified,
        "unverified": unverified,
        "scams":      scams,
        "sources":    sources,
    }


# Admin endpoints removed per user request; API now always computes
# categories from titles and does not expose admin preview.


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=False)
