"""Reads the register workbook: the master list of projects."""
from __future__ import annotations

import re

from ..excel import (Workbook, find_header_row, map_headers, named_header_count,
                     unnamed_columns_with_data)
from ..textnorm import as_text

KIND = "register"

# Field name -> spellings of the header. Matching is by name, with typos allowed.
HEADERS = {
    "name": ["project name", "project"],
    "client": ["client", "customer", "client name"],
    "value": ["project value mvr", "project value", "contract value", "value mvr", "value"],
    "request_date": ["request date"],
    "status": ["status", "project status", "updates"],
    "order_type": ["order type"],
    "pr_number": ["pr number", "pr no"],
    "pr_date": ["pr date"],
    "delivery_period": ["agreed delivery period", "delivery period", "delivery days"],
    "so_number": ["so number", "so no", "sales order", "sales order number"],
    "remarks": ["remarks", "remark", "notes"],
    # optional columns the app prefers when they are filled in
    "agreement_date": ["agreement date", "agreement signed date", "signed date"],
    "due_date": ["due date", "deadline", "delivery due date"],
    "delivery_status": ["delivery status"],
    "next_action": ["next action", "next step"],
    "payment_status": ["payment status", "payment"],
    "project_id": ["project id", "project code"],
}

_OTHER_SHEETS = re.compile(r"correction|link|invoice", re.IGNORECASE)


def find_master_sheet(workbook: Workbook):
    """The sheet with a "Project name" header and the most named header cells."""
    best = None
    for sheet in workbook.sheets:
        if _OTHER_SHEETS.search(sheet.name):
            continue
        row = find_header_row(sheet, [["project name"]])
        if row is None:
            continue
        count = named_header_count(sheet, row)
        if best is None or count > best[2]:
            best = (sheet, row, count)
    return best


def read(workbook: Workbook, reading, cfg: dict, recognised: list[str]) -> str | None:
    from . import RegisterRow, RegisterTable

    best = find_master_sheet(workbook)
    if best is None:
        return None
    sheet, header_row, _count = best
    header_cells = sheet.rows[header_row - 1]
    columns = map_headers(header_cells, HEADERS)
    if "name" not in columns:
        return None

    # The payment status sits in the first column after REMARKS that has no header.
    payment_col = columns.get("payment_status")
    if payment_col is None:
        last_named = max((c for c, v in enumerate(header_cells, start=1) if as_text(v).strip()),
                         default=0)
        after = columns.get("remarks", last_named)
        unnamed = unnamed_columns_with_data(sheet, header_row, after_col=after)
        payment_col = unnamed[0] if unnamed else None

    labels: dict[int, str] = {}
    for c in range(1, sheet.n_cols + 1):
        text = as_text(sheet.cell(header_row, c)).strip()
        if text:
            labels[c] = text
        elif c == payment_col:
            labels[c] = "Payment status (column without a header)"

    table = RegisterTable(workbook.name, sheet.name, header_row, columns,
                          mtime=workbook.path.stat().st_mtime)
    for r in range(header_row + 1, sheet.n_rows + 1):
        name = as_text(sheet.cell(r, columns["name"])).strip()
        if not name:
            continue                                   # total row, legend rows, blank rows
        cells = {f: sheet.cell(r, c) for f, c in columns.items()}
        raw = {}
        for c in range(1, sheet.n_cols + 1):
            value = sheet.cell(r, c)
            if as_text(value).strip():
                raw[labels.get(c, f"Column {c} (no header)")] = value
        table.rows.append(RegisterRow(
            row=r, cells=cells, raw=raw,
            payment_cell=sheet.cell(r, payment_col) if payment_col else None,
            hidden=r in sheet.hidden_rows))
    reading.registers.append(table)
    ignored = [s.name for s in workbook.sheets
               if s.name != sheet.name and not _OTHER_SHEETS.search(s.name)]
    extra = f"; sheets not used: {', '.join(ignored)}" if ignored else ""
    return (f"register: {len(table.rows)} projects from sheet '{sheet.name}' "
            f"(headers in row {header_row}){extra}")
