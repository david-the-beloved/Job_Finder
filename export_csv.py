# export_csv.py
# Exports jobs to CSV files for backup and sharing.

from __future__ import annotations

import csv
import os
from datetime import datetime

from database import get_all_jobs


CSV_HEADERS = [
    "id",
    "source",
    "title",
    "company",
    "location",
    "salary",
    "remote",
    "description",
    "url",
    "date_posted",
    "date_found",
    "verified",
    "scam_flag",
    "quality_score",
    "tech_stack",
    "still_active",
    "last_checked",
]


def _job_to_row(job: dict) -> list:
    return [
        job.get("id", ""),
        job.get("source", ""),
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("salary", ""),
        job.get("remote", ""),
        job.get("description", ""),
        job.get("url", ""),
        job.get("date_posted", ""),
        job.get("date_found", ""),
        job.get("verified", ""),
        job.get("scam_flag", ""),
        job.get("quality_score", ""),
        job.get("tech_stack", "") or "",
        job.get("still_active", ""),
        job.get("last_checked", ""),
    ]


def _write_csv(path: str, headers: list[str], rows: list[list]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        writer.writerows(rows)


def export_csv() -> str:
    """Export dated and rolling CSV files. Returns the rolling CSV path."""
    os.makedirs("data", exist_ok=True)

    all_jobs = get_all_jobs()
    scams = [job for job in all_jobs if job.get("scam_flag")]

    date_stamp = datetime.now().strftime("%Y-%m-%d")

    dated_path = os.path.join("data", f"jobs_export_{date_stamp}.csv")
    latest_path = os.path.join("data", "jobs_latest.csv")
    scams_path = os.path.join("data", f"scams_{date_stamp}.csv")

    all_rows = [_job_to_row(job) for job in all_jobs]
    scam_rows = [_job_to_row(job) for job in scams]

    _write_csv(dated_path, CSV_HEADERS, all_rows)
    _write_csv(latest_path, CSV_HEADERS, all_rows)
    _write_csv(scams_path, CSV_HEADERS, scam_rows)

    print(f"  CSV saved -> {dated_path}")
    print(f"  CSV saved -> {latest_path}")
    print(f"  CSV saved -> {scams_path}")

    return latest_path


if __name__ == "__main__":
    export_csv()
