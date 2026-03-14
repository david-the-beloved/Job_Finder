# export_sheets.py
# Mirrors database export data to Google Sheets using a service account.

from __future__ import annotations

import json
import os
from datetime import datetime, date

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from config import (
    GOOGLE_SERVICE_ACCOUNT_KEY,
    GOOGLE_SHEET_ID,
    MIN_QUALITY_SCORE,
    GEMINI_QUOTA_FILE,
)
from database import get_connection, get_jobs_for_export, get_all_jobs, get_stats


JOB_TAB = "Job Postings"
SUMMARY_TAB = "Summary"
SCAM_TAB = "Scam Flags"

JOB_HEADERS = [
    "ID",
    "Source",
    "Job Title",
    "Company",
    "Location",
    "Salary",
    "Remote",
    "Tech Stack",
    "Score",
    "Date Posted",
    "Date Found",
    "Link",
    "Verified",
    "Description",
]

SCAM_HEADERS = ["Title", "Company", "Source", "Scam Reason", "Score", "URL"]


def _get_ai_stats() -> dict:
    conn = get_connection()
    scams_total = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE scam_flag != '' AND scam_flag IS NOT NULL"
    ).fetchone()[0]
    verified_total = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE verified = 1").fetchone()[0]
    unverified = conn.execute(
        "SELECT COUNT(*) FROM jobs WHERE verified IS NULL").fetchone()[0]
    avg_row = conn.execute(
        "SELECT AVG(quality_score) FROM jobs WHERE quality_score IS NOT NULL"
    ).fetchone()[0]
    avg_score = round(avg_row, 1) if avg_row else "--"
    conn.close()

    calls_today = 0
    cost_today = 0.0

    try:
        if os.path.exists(GEMINI_QUOTA_FILE):
            with open(GEMINI_QUOTA_FILE, "r", encoding="utf-8") as f:
                quota = json.load(f)
            if quota.get("date") == str(date.today()):
                calls_today = quota.get("calls", 0)
                cost_today = quota.get("cost_usd", 0.0)
    except Exception:
        pass

    return {
        "scams_total": scams_total,
        "verified_total": verified_total,
        "unverified": unverified,
        "avg_score": avg_score,
        "calls_today": calls_today,
        "cost_today": cost_today,
    }


def _job_to_row(job: dict) -> list:
    score = job.get("quality_score")
    verified = job.get("verified")
    verified_label = "✓" if verified == 1 else ("✗" if verified == 0 else "—")

    return [
        job.get("id", ""),
        job.get("source", ""),
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("salary", ""),
        job.get("remote", ""),
        job.get("tech_stack", "") or "",
        score if score is not None else "—",
        job.get("date_posted", ""),
        (job.get("date_found", "") or "")[:10],
        job.get("url", ""),
        verified_label,
        (job.get("description", "") or "")[:300],
    ]


def _build_summary_rows(stats: dict, ai_stats: dict) -> list[list]:
    rows = [
        ["Metric", "Value"],
        ["Last updated", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Total jobs in database", stats.get("total", 0)],
        ["Added today", stats.get("today", 0)],
        ["Remote jobs", stats.get("remote", 0)],
        ["Scams flagged", ai_stats.get("scams_total", 0)],
        ["Unverified (pending AI)", ai_stats.get("unverified", 0)],
        ["Verified jobs", ai_stats.get("verified_total", 0)],
        ["Avg quality score", ai_stats.get("avg_score", "--")],
        ["API calls today", ai_stats.get("calls_today", 0)],
        ["Est. cost today", f"${ai_stats.get('cost_today', 0.0):.4f}"],
        [],
        ["Jobs by Source", "Count"],
    ]

    for source, count in stats.get("sources", {}).items():
        rows.append([source, count])

    return rows


def _ensure_tabs(service, spreadsheet_id: str, tab_names: list[str]) -> dict[str, int]:
    meta = (
        service.spreadsheets()
        .get(spreadsheetId=spreadsheet_id, fields="sheets(properties(sheetId,title))")
        .execute()
    )

    existing = {
        s["properties"]["title"]: s["properties"]["sheetId"]
        for s in meta.get("sheets", [])
    }

    requests = []
    for title in tab_names:
        if title not in existing:
            requests.append({"addSheet": {"properties": {"title": title}}})

    if requests:
        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body={"requests": requests},
        ).execute()

        meta = (
            service.spreadsheets()
            .get(spreadsheetId=spreadsheet_id, fields="sheets(properties(sheetId,title))")
            .execute()
        )
        existing = {
            s["properties"]["title"]: s["properties"]["sheetId"]
            for s in meta.get("sheets", [])
        }

    return existing


def _format_headers(service, spreadsheet_id: str, sheet_ids: dict[str, int]):
    header_bg = {"red": 0.102, "green": 0.235, "blue": 0.431}
    white = {"red": 1.0, "green": 1.0, "blue": 1.0}

    requests = []
    for title in [JOB_TAB, SUMMARY_TAB, SCAM_TAB]:
        requests.append(
            {
                "repeatCell": {
                    "range": {
                        "sheetId": sheet_ids[title],
                        "startRowIndex": 0,
                        "endRowIndex": 1,
                    },
                    "cell": {
                        "userEnteredFormat": {
                            "backgroundColor": header_bg,
                            "textFormat": {"bold": True, "foregroundColor": white},
                            "horizontalAlignment": "CENTER",
                        }
                    },
                    "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment)",
                }
            }
        )
        requests.append(
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": sheet_ids[title],
                        "gridProperties": {"frozenRowCount": 1},
                    },
                    "fields": "gridProperties.frozenRowCount",
                }
            }
        )

    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": requests},
    ).execute()


def export_to_sheets() -> str:
    """Export database jobs and summaries to Google Sheets and return sheet URL."""
    if not GOOGLE_SHEET_ID:
        raise ValueError(
            "GOOGLE_SHEET_ID is empty. Set it in config or environment.")

    if not os.path.exists(GOOGLE_SERVICE_ACCOUNT_KEY):
        raise FileNotFoundError(
            f"Service account key not found at: {GOOGLE_SERVICE_ACCOUNT_KEY}"
        )

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(
        GOOGLE_SERVICE_ACCOUNT_KEY, scopes=scopes)
    service = build("sheets", "v4", credentials=creds, cache_discovery=False)

    sheet_ids = _ensure_tabs(service, GOOGLE_SHEET_ID, [
                             JOB_TAB, SUMMARY_TAB, SCAM_TAB])

    # Clear existing data before writing fresh data.
    service.spreadsheets().values().batchClear(
        spreadsheetId=GOOGLE_SHEET_ID,
        body={
            "ranges": [
                f"'{JOB_TAB}'!A:Z",
                f"'{SUMMARY_TAB}'!A:Z",
                f"'{SCAM_TAB}'!A:Z",
            ]
        },
    ).execute()

    jobs = get_jobs_for_export(min_quality=MIN_QUALITY_SCORE)
    all_jobs = get_all_jobs()
    stats = get_stats()
    ai_stats = _get_ai_stats()

    job_rows = [JOB_HEADERS] + [_job_to_row(job) for job in jobs]

    scam_jobs = [j for j in all_jobs if j.get("scam_flag")]
    scam_rows = [SCAM_HEADERS]
    for job in scam_jobs:
        scam_rows.append(
            [
                job.get("title", ""),
                job.get("company", ""),
                job.get("source", ""),
                job.get("scam_flag", ""),
                job.get("quality_score", ""),
                job.get("url", ""),
            ]
        )

    summary_rows = _build_summary_rows(stats, ai_stats)

    service.spreadsheets().values().update(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{JOB_TAB}'!A1",
        valueInputOption="RAW",
        body={"values": job_rows},
    ).execute()

    service.spreadsheets().values().update(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{SUMMARY_TAB}'!A1",
        valueInputOption="RAW",
        body={"values": summary_rows},
    ).execute()

    service.spreadsheets().values().update(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=f"'{SCAM_TAB}'!A1",
        valueInputOption="RAW",
        body={"values": scam_rows},
    ).execute()

    _format_headers(service, GOOGLE_SHEET_ID, sheet_ids)

    sheet_url = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}"
    print(f"  Google Sheets updated -> {sheet_url}")
    print(
        f"  Tabs: {JOB_TAB} ({len(jobs)} jobs)  |  {SCAM_TAB} ({len(scam_jobs)})  |  {SUMMARY_TAB}"
    )
    return sheet_url


if __name__ == "__main__":
    export_to_sheets()
