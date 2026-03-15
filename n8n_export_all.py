# n8n_export_all.py
# Exports ALL jobs from DB regardless of date.
# Use for one-time full sync or manual resets.

from config import MIN_QUALITY_SCORE
from database import get_connection, init_db
import sys
import json
import os
import io
import contextlib
from datetime import datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '.')


with contextlib.redirect_stdout(io.StringIO()):
    init_db()


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


conn = get_connection()
rows = conn.execute("""
    SELECT id, source, title, company, location, salary, remote,
           tech_stack, quality_score, date_posted, date_found,
           url, verified, scam_flag, description
    FROM jobs
    WHERE (scam_flag IS NULL OR scam_flag = '')
      AND (quality_score IS NULL OR quality_score >= ?)
    ORDER BY quality_score DESC, date_found DESC
""", (MIN_QUALITY_SCORE,)).fetchall()
conn.close()

jobs = []
for r in rows:
    jobs.append({
        "ID":           r[0] or "",
        "Source":       r[1] or "",
        "Title":        r[2] or "",
        "Company":      r[3] or "",
        "Location":     r[4] or "",
        "Salary":       r[5] or "",
        "Remote":       r[6] or "",
        "Tech Stack":   r[7] or "",
        "Score":        r[8] if r[8] is not None else "",
        "Date Posted":  _fmt_date(r[9] or ""),
        "Date Found":   _fmt_date(r[10] or ""),
        "URL":          r[11] or "",
        "Verified":     _fmt_verified(r[12]),
        "Description":  (r[14] or "")[:300],
    })

print(json.dumps(jobs))
