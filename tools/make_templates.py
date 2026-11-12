"""Writes the ready-to-use Excel templates into the ``templates`` folder.

Run ``python tools/make_templates.py``. The templates only use header names the
app already understands, with drop-down lists so the values are always typed
the same way.
"""
from __future__ import annotations

import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from projectdash import model as M  # noqa: E402
from projectdash.resolve import FIELD_HELP  # noqa: E402

HEAD_FILL = PatternFill("solid", fgColor="1F2937")
NEW_FILL = PatternFill("solid", fgColor="2A78D6")
LINE_STATUSES = ["Delivered", "Partial", "Pending", "Out of stock", "Re-ordered", "Cancelled"]
GI_NOTES = ["NEED TO MAKE GI", "NEED TO REVERSE GI", "GI DONE"]


def _header(ws, headers, new=(), widths=None, row=1):
    for c, h in enumerate(headers, start=1):
        cell = ws.cell(row, c, h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = NEW_FILL if h in new else HEAD_FILL
        cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.column_dimensions[cell.column_letter].width = (widths or {}).get(h, max(12, len(h) + 4))
    ws.freeze_panes = ws.cell(row + 1, 1)


def _dropdown(ws, column_letter, choices, first_row=2, last_row=1000):
    dv = DataValidation(type="list", formula1='"' + ",".join(choices) + '"', allow_blank=True)
    dv.error = "Please pick a value from the list."
    dv.errorTitle = "Not in the list"
    ws.add_data_validation(dv)
    dv.add(f"{column_letter}{first_row}:{column_letter}{last_row}")


def _notes(wb, title, lines):
    ws = wb.create_sheet(title)
    for i, line in enumerate(lines, start=1):
        cells = line if isinstance(line, tuple) else (line,)
        for c, text in enumerate(cells, start=1):
            ws.cell(i, c, text)
    ws["A1"].font = Font(bold=True, size=13)
    ws.column_dimensions["A"].width = 34
    ws.column_dimensions["B"].width = 90
    return ws


def corrections_template(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Corrections"
    _header(ws, ["project", "field", "value", "note"],
            widths={"project": 60, "field": 20, "value": 24, "note": 60})
    _dropdown(ws, "B", M.CORRECTION_FIELDS)
    links = wb.create_sheet("Links")
    _header(links, ["file", "project"], widths={"file": 50, "project": 60})
    _notes(wb, "How to use", [
        "Corrections and Links",
        "Save a copy of this file in the app's data folder. Any file name works.",
        "The app never changes your original files. A correction only changes what the app shows.",
        "",
        "CORRECTIONS sheet: one row fixes one value of one project.",
        ("project", "The project name, or any part of it that only one project contains."),
        ("field", "Pick from the list (see below)."),
        ("value", "The correct value."),
        ("note", "Optional. Why you changed it. Shown next to the value in the app."),
        "",
        ("field", "what to type in 'value'"),
        *[(f, FIELD_HELP[f]) for f in M.CORRECTION_FIELDS],
        "",
        "Example row:   Lagoon City water meters | delivery_days | 90 | from the signed agreement",
        "",
        "LINKS sheet: tells the app which project a detail file belongs to.",
        ("file", "The file name, or any part of it."),
        ("project", "The project name, or any part of it that only one project contains."),
        "Only needed when the app cannot match a file by its customer code or Sales Order.",
    ])
    wb.save(path)


DETAIL_HEADERS = ["#", "Customer Name", "Site / Lot", "Article", "Description", "Unit", "Quantity",
                  "Delivered Qty", "Balance Qty", "Unit price", "Value", "Vendor", "Vendor Qtn No",
                  "Quotation", "SAP Quotation", "Sales Order", "PR / PO", "Client PO",
                  "Delivery Note", "Invoice", "Dispatched date", "ETA", "Line status", "Remarks",
                  "GI note"]
DETAIL_NEW = ("Site / Lot", "Unit price", "Value", "ETA", "Line status", "GI note")


def detail_template(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Items"
    _header(ws, DETAIL_HEADERS, new=DETAIL_NEW,
            widths={"Description": 46, "Customer Name": 34, "Remarks": 30, "#": 6})
    col = {h: ws.cell(1, i).column_letter for i, h in enumerate(DETAIL_HEADERS, start=1)}
    for r in range(2, 202):
        ws[f"{col['Balance Qty']}{r}"] = (
            f'=IF({col["Quantity"]}{r}="","",{col["Quantity"]}{r}-{col["Delivered Qty"]}{r})')
        ws[f"{col['Value']}{r}"] = (
            f'=IF(OR({col["Quantity"]}{r}="",{col["Unit price"]}{r}=""),"",'
            f'{col["Quantity"]}{r}*{col["Unit price"]}{r})')
        for name in ("Dispatched date", "ETA"):
            ws[f"{col[name]}{r}"].number_format = "DD.MM.YYYY"
    _dropdown(ws, col["Line status"], LINE_STATUSES)
    _dropdown(ws, col["GI note"], GI_NOTES)
    _notes(wb, "How to use", [
        "Project detail file (one per project)",
        "Name the file with the customer code and project, e.g. '20004567 - Department of Public Works.xlsx'.",
        "Blue headers are new, optional columns. Everything else is what you already keep.",
        "",
        ("Site / Lot", "For projects with several sites, houses or delivery lots. Leave empty otherwise."),
        ("Unit price", "Fill it and Value calculates itself. With values on every line, progress is measured by value."),
        ("ETA", "A real date (with the year) for lines not yet delivered. The app warns when an ETA is after the due date."),
        ("Line status", "Pick from the list. It always beats what the quantities say."),
        ("GI note", "Pick the SAP goods-issue to-do, or leave empty."),
        ("Remarks", "Free text, as before."),
        "",
        "When an item is re-ordered: set the ORIGINAL line to 'Re-ordered' and add the new order as a new row.",
        "Keep one article number for one kind of item where you can.",
        "You do not need to fill group columns (Quotation, Sales Order, PR / PO) on every row of a vendor.",
    ])
    wb.save(path)


REGISTER_HEADERS = ["Project ID", "Project name", "Client", "Project value MVR", "Request date",
                    "Agreement date", "Agreed delivery period", "Due date", "Delivery status",
                    "Payment status", "Next action", "Status", "Order Type", "PR Number", "PR Date",
                    "SO number", "REMARKS"]
REGISTER_NEW = ("Project ID", "Agreement date", "Due date", "Delivery status", "Payment status",
                "Next action")


def register_template(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Projects"
    _header(ws, REGISTER_HEADERS, new=REGISTER_NEW,
            widths={"Project name": 54, "Status": 50, "REMARKS": 50, "Next action": 34, "Client": 26})
    col = {h: ws.cell(1, i).column_letter for i, h in enumerate(REGISTER_HEADERS, start=1)}
    _dropdown(ws, col["Delivery status"], M.DELIVERY_STATUSES)
    _dropdown(ws, col["Payment status"], M.PAYMENT_LABELS[:5])
    for r in range(2, 302):
        for name in ("Request date", "Agreement date", "Due date", "PR Date"):
            ws[f"{col[name]}{r}"].number_format = "DD.MM.YYYY"
        ws[f"{col['Project value MVR']}{r}"].number_format = "#,##0.00"
    _notes(wb, "How to use", [
        "Master list of projects",
        "You can keep using your current sheet. To get the benefit, add any of the blue columns to it;",
        "the app finds columns by their header name, so their position does not matter.",
        "",
        ("Project ID", "A short code you never change (e.g. P-2025-014). Lets files and corrections find the project even if it is renamed."),
        ("Agreement date", "The date the agreement was signed, as a real date."),
        ("Agreed delivery period", "Number of days, e.g. 45. With the agreement date this gives the due date."),
        ("Due date", "Only when the due date is NOT agreement date + delivery period."),
        ("Delivery status", "Pick from the list. Beats whatever the notes say."),
        ("Payment status", "Pick from the list. This is the column that has no header today."),
        ("Next action", "A few words: what happens next and who does it."),
        ("Status / REMARKS", "Keep writing your diary here. Start each new line with the date, e.g. 05.11.2025 - 1st lot delivered."),
    ])
    wb.save(path)


if __name__ == "__main__":
    out = ROOT / "templates"
    out.mkdir(exist_ok=True)
    corrections_template(out / "Corrections and Links.xlsx")
    detail_template(out / "Project detail file.xlsx")
    register_template(out / "Project register.xlsx")
    print(f"Templates written to {out}")
