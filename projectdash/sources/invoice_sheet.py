"""Reads the INVOICE sheet of the register workbook.

Used only as a cross-check: it can supply an invoice amount the notes leave
out, and it is compared with the payment status typed in the master list.
"""
from __future__ import annotations

import re

from ..excel import Workbook, find_header_row, map_headers
from ..textnorm import as_text, to_date, to_number

KIND = "invoice sheet"

_HEADERS = {
    "number": ["invoice number", "invoice no", "invoice"],
    "amount": ["amount mvr", "amount", "invoice amount", "value"],
    "project": ["project", "project name", "description"],
    "customer": ["customer", "client"],
    "dispatched": ["dispatched date", "dispatch date", "invoice date"],
    "status": ["payment status", "status"],
}
_NUMBER = re.compile(r"^(61\d{8}|92\d{7})$")


def read(workbook: Workbook, reading, cfg: dict, recognised: list[str]) -> str | None:
    from . import InvoiceRow

    if not cfg.get("use_invoice_sheet", True):
        return None
    n = 0
    for sheet in workbook.sheets:
        if not re.search(r"invoice", sheet.name, re.IGNORECASE):
            continue
        row = find_header_row(sheet, [_HEADERS["number"], ["amount mvr", "amount"]])
        if row is None:
            continue
        cols = map_headers(sheet.rows[row - 1], _HEADERS)
        if "number" not in cols:
            continue
        for r in range(row + 1, sheet.n_rows + 1):
            number = as_text(sheet.cell(r, cols["number"])).strip()
            if not _NUMBER.match(number):
                continue

            def get(name: str):
                return sheet.cell(r, cols[name]) if name in cols else None

            status = get("status")
            reading.invoice_rows.append(InvoiceRow(
                number=number,
                amount=to_number(get("amount")),
                project_text=" ".join(as_text(get("project")).split()),
                customer=as_text(get("customer")).strip(),
                status=" ".join(as_text(status).split()),
                dispatched=to_date(get("dispatched"))))
            n += 1
    return f"{n} invoices from the INVOICE sheet (cross-check only)" if n else None
