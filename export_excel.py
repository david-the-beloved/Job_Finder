# ─────────────────────────────────────────────────────────────
# export_excel.py  —  Export jobs from SQLite → Excel
# ─────────────────────────────────────────────────────────────

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from datetime import datetime
import os

from database import get_all_jobs, get_stats
from config import EXCEL_PATH


# ── Colour palette ────────────────────────────────────────────
C = {
    "header_bg":    "1A3C6E",
    "header_fg":    "FFFFFF",
    "row_even":     "F2F7FF",
    "row_odd":      "FFFFFF",
    "remote_yes":   "D4EDDA",
    "remote_hybrid":"FFF3CD",
    "remote_no":    "F8D7DA",
    "scam":         "FF4444",
    "verified_yes": "28A745",
    "verified_no":  "DC3545",
    "source_indeed":"2557A7",
    "source_remote":"0D8050",
    "source_hn":    "FF6600",
    "source_google":"4285F4",
    "source_other": "666666",
    "summary_bg":   "E8EEF7",
    "accent":       "1A3C6E",
}

COLUMNS = [
    ("ID",           8),
    ("Source",      16),
    ("Job Title",   36),
    ("Company",     22),
    ("Location",    18),
    ("Salary",      18),
    ("Remote",      10),
    ("Date Posted", 13),
    ("Date Found",  13),
    ("Link",        14),
    ("Verified",    11),
    ("Scam Flag",   18),
    ("Description", 55),
]

thin    = Side(style="thin",   color="DDDDDD")
thick   = Side(style="medium", color="AAAAAA")
BORDER  = Border(left=thin, right=thin, top=thin, bottom=thin)
H_BORDER = Border(left=thick, right=thick, top=thick, bottom=thick)


def _source_color(source: str) -> str:
    s = source.lower()
    if "indeed"   in s: return C["source_indeed"]
    if "remoteok" in s: return C["source_remote"]
    if "hacker"   in s: return C["source_hn"]
    if "google"   in s: return C["source_google"]
    return C["source_other"]


def _write_header(ws):
    fill = PatternFill("solid", fgColor=C["header_bg"])
    for col, (label, width) in enumerate(COLUMNS, 1):
        cell = ws.cell(row=1, column=col, value=label)
        cell.font      = Font(name="Arial", size=11, bold=True, color=C["header_fg"])
        cell.fill      = fill
        cell.border    = H_BORDER
        cell.alignment = Alignment(horizontal="center", vertical="center")
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[1].height = 28
    ws.freeze_panes  = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(COLUMNS))}1"


def _write_row(ws, row_num: int, job: dict):
    is_even = (row_num % 2 == 0)
    base_fill = PatternFill("solid", fgColor=C["row_even"] if is_even else C["row_odd"])

    values = [
        job.get("id",          ""),
        job.get("source",      ""),
        job.get("title",       ""),
        job.get("company",     ""),
        job.get("location",    ""),
        job.get("salary",      ""),
        job.get("remote",      ""),
        job.get("date_posted", ""),
        job.get("date_found",  "")[:10] if job.get("date_found") else "",
        job.get("url",         ""),
        "✓" if job.get("verified") == 1 else ("✗" if job.get("verified") == 0 else "—"),
        job.get("scam_flag",   "") or "",
        job.get("description", "")[:300],
    ]

    for col, val in enumerate(values, 1):
        cell = ws.cell(row=row_num, column=col, value=val)
        cell.border    = BORDER
        cell.alignment = Alignment(vertical="top", wrap_text=(col == 13))
        cell.font      = Font(name="Arial", size=10)
        cell.fill      = base_fill

        # Source — coloured text
        if col == 2:
            cell.font = Font(name="Arial", size=10, bold=True,
                             color=_source_color(str(val)))

        # Remote pill
        if col == 7:
            v = str(val)
            bg = (C["remote_yes"]    if v == "Yes"
                  else C["remote_hybrid"] if v == "Hybrid"
                  else C["remote_no"])
            cell.fill      = PatternFill("solid", fgColor=bg)
            cell.font      = Font(name="Arial", size=10, bold=True)
            cell.alignment = Alignment(horizontal="center", vertical="top")

        # Hyperlink
        if col == 10 and str(val).startswith("http"):
            cell.hyperlink = str(val)
            cell.value     = "🔗 View Job"
            cell.font      = Font(name="Arial", size=10,
                                  color="0A66C2", underline="single")

        # Verified
        if col == 11:
            color = (C["verified_yes"] if val == "✓"
                     else C["verified_no"] if val == "✗"
                     else "888888")
            cell.font = Font(name="Arial", size=10, bold=True, color=color)
            cell.alignment = Alignment(horizontal="center", vertical="top")

        # Scam flag
        if col == 12 and val:
            cell.font = Font(name="Arial", size=10, color=C["scam"], bold=True)


def _write_summary(wb, stats: dict):
    if "📊 Summary" in wb.sheetnames:
        del wb["📊 Summary"]
    ws = wb.create_sheet("📊 Summary", 0)

    accent_fill = PatternFill("solid", fgColor=C["accent"])
    grey_fill   = PatternFill("solid", fgColor=C["summary_bg"])

    def row(r, label, value, bold_val=False):
        c1 = ws.cell(row=r, column=1, value=label)
        c2 = ws.cell(row=r, column=2, value=value)
        c1.font = Font(name="Arial", size=11)
        c2.font = Font(name="Arial", size=11, bold=bold_val)
        c1.alignment = c2.alignment = Alignment(vertical="center")

    ws.cell(row=1, column=1, value="📊 Job Scraper — Summary").font = Font(
        name="Arial", size=15, bold=True, color=C["accent"])
    ws.cell(row=2, column=1, value=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}").font = Font(
        name="Arial", size=10, color="888888")

    ws.append([])
    row(4, "Total Jobs",          stats.get("total", 0),  True)
    row(5, "Added Today",         stats.get("today", 0),  True)
    row(6, "Remote Jobs",         stats.get("remote", 0), True)

    ws.append([])
    ws.cell(row=8, column=1, value="Jobs by Source").font = Font(
        name="Arial", size=12, bold=True)

    for i, (source, count) in enumerate(stats.get("sources", {}).items(), 9):
        ws.cell(row=i, column=1, value=source).font  = Font(name="Arial", size=11)
        ws.cell(row=i, column=2, value=count).font   = Font(name="Arial", size=11, bold=True)
        if i % 2 == 0:
            for c in [1, 2]:
                ws.cell(row=i, column=c).fill = grey_fill

    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 15


def export(jobs: list[dict] = None) -> str:
    """
    Write all jobs (or provided list) to Excel.
    Returns the file path.
    """
    jobs = jobs or get_all_jobs()
    stats = get_stats()

    wb = Workbook()
    ws = wb.active
    ws.title = "Job Postings"

    _write_header(ws)
    for i, job in enumerate(jobs):
        _write_row(ws, i + 2, job)

    ws.row_dimensions[1].height = 28

    _write_summary(wb, stats)

    # Make summary the active sheet on open
    wb.active = wb["📊 Summary"]

    os.makedirs(os.path.dirname(EXCEL_PATH) if os.path.dirname(EXCEL_PATH) else ".", exist_ok=True)
    wb.save(EXCEL_PATH)
    print(f"  ✓ Excel saved → {EXCEL_PATH}  ({len(jobs)} jobs)")
    return EXCEL_PATH


if __name__ == "__main__":
    export()
