"""Files the app hands back: a pre-filled Corrections sheet and the table view."""
from __future__ import annotations

import io
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from . import model as M
from .resolve import FIELD_HELP

_HEAD = PatternFill("solid", fgColor="1F2937")


def corrections_workbook(portfolio: M.Portfolio) -> bytes:
    """An Excel file with one row per missing value, ready to fill in.

    Saved into the data folder (any file name), the app reads it on the next
    refresh. Rows with an empty value are ignored, so nothing has to be deleted.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Corrections"
    ws.append(["project", "field", "value", "note"])
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = _HEAD
    for p in portfolio.projects:
        for field in p.missing:
            ws.append([p.name, field, None, f"Type the {FIELD_HELP.get(field, field)}"])
    for col, width in zip("ABCD", (60, 20, 24, 70)):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"
    choices = DataValidation(type="list", formula1='"' + ",".join(M.CORRECTION_FIELDS) + '"',
                             allow_blank=True)
    choices.error = "Pick a field from the list."
    ws.add_data_validation(choices)
    choices.add("B2:B2000")

    how = wb.create_sheet("How to use")
    rows = [
        ("How this file works",),
        ("1. Type the missing value in the 'value' column. Leave a row empty to skip it.",),
        ("2. Save this file into the app's data folder (any file name is fine).",),
        ("3. Refresh the dashboard. Corrected values are labelled 'correction'.",),
        ("",),
        ("You can add your own rows. 'project' may be the full project name or any part of it "
         "that only one project contains.",),
        ("",),
        ("field", "what to type in 'value'"),
    ] + [(f, FIELD_HELP[f]) for f in M.CORRECTION_FIELDS]
    for row in rows:
        how.append(list(row))
    how["A1"].font = Font(bold=True, size=13)
    how["A8"].font = how["B8"].font = Font(bold=True)
    how.column_dimensions["A"].width = 24
    how.column_dimensions["B"].width = 80
    for row in how.iter_rows(min_row=2, max_row=6):
        row[0].alignment = Alignment(wrap_text=False)
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def table_rows(portfolio: M.Portfolio) -> list[dict[str, Any]]:
    """One flat row per project for the table view and for downloading."""
    rows = []
    for p in portfolio.projects:
        pr = p.progress
        rows.append({
            "key": p.key,
            "Project": p.name,
            "Client": p.client,
            "Status": p.status,
            "Delivery": p.get("delivery_status"),
            "Delivered %": pr.percent if pr and pr.percent is not None else None,
            "Value": p.get("contract_value"),
            "Agreement date": p.get("agreement_date"),
            "Delivery days": p.get("delivery_days"),
            "Due date": p.get("due_date"),
            "Days to due": p.days_to_due if p.status not in (M.S_COMPLETE, M.S_PIPELINE) else None,
            "Payment": p.get("payment_status"),
            "Invoiced": p.get("invoiced"),
            "Unpaid": p.get("unpaid"),
            "Last activity": p.last_activity,
            "Needs attention": len(p.attention),
            "Order type": p.get("order_type"),
            "Request date": p.get("request_date"),
            "PR number": p.get("pr_number"),
            "PR date": p.get("pr_date"),
            "SO number": p.get("so_number"),
            "Invoices": ", ".join(i.number for i in p.invoices),
            "Next action": p.get("next_action"),
            "Detail file": ", ".join(f.name for f in p.detail_files),
            "Status notes": " | ".join(t for t in [p.status_text.strip()] if t),
            "Remarks": p.remarks_text.strip(),
            "Register row": p.row,
        })
    return rows
