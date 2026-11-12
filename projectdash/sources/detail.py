"""Reads a project detail file ("master sheet"): the line items of one project.

Detail files differ from project to project, so nothing here depends on column
positions or on a fixed set of columns. A sheet is used when it has a header row
with a description and a quantity; columns the app doesn't know are kept and shown.
"""
from __future__ import annotations

import re
from collections import Counter

from .. import model as M
from ..excel import Sheet, Workbook, find_header_row, map_headers
from ..lines import analyse
from ..textnorm import as_text, find_dates, is_blank, to_date, to_number

KIND = "detail file"

HEADERS = {
    "num": ["#", "item no", "line", "line no", "sr no", "serial no"],
    "customer": ["customer name", "customer", "client", "client name"],
    "article": ["article", "article no", "article number", "material", "material no",
                "item code", "code", "sku"],
    "description": ["description", "item description", "material description", "item",
                    "items", "particulars", "product"],
    "unit": ["unit", "uom", "units"],
    "qty": ["quantity", "qty", "order qty", "ordered qty", "required qty", "total qty"],
    "delivered": ["delivered qty", "delivered", "delivered quantity", "qty delivered",
                  "supplied qty", "issued qty"],
    "balance": ["balance qty", "balance", "balance quantity", "pending qty", "remaining qty"],
    "vendor": ["vendor", "supplier", "vendor name"],
    "vendor_quote": ["vendor qtn no", "vendor quotation", "vendor quote", "vendor qtn",
                     "vendor quotation no"],
    "quotation": ["quotation", "quotation no", "our quotation"],
    "sap_quotation": ["sap quotation", "sap quotation no"],
    "sales_order": ["sales order", "sales order no", "so", "so number", "so no"],
    "pr_po": ["pr po", "pr", "po", "pr number", "po number", "purchase order"],
    "client_po": ["client po", "customer po", "client po no"],
    "delivery_note": ["delivery note", "delivery note no", "dn", "dn no", "dn number"],
    "invoice": ["invoice", "invoice no", "invoice number"],
    "value": ["value", "line value", "amount", "total value", "total", "total price"],
    "unit_price": ["unit price", "rate", "price", "unit rate"],
    "dispatched": ["dispatched date", "dispatch date", "delivered date", "delivery date"],
    "remarks": ["remarks", "remark", "status", "line status", "delivery status"],
    "eta": ["eta", "expected date", "expected delivery", "eta date"],
    "site": ["site", "lot", "location", "island", "site lot"],
}

# Columns that are only typed on the first row of a group.
GROUP_FIELDS = ("quotation", "sap_quotation", "sales_order", "pr_po")

_CODE = re.compile(r"(?<!\d)(\d{6,})(?!\d)")
_TOTAL_ROW = re.compile(r"^\s*(grand\s+)?(sub\s*)?total\b", re.IGNORECASE)


def _clean(value) -> str:
    return "" if is_blank(value) else " ".join(as_text(value).split())


def _group_value(sheet: Sheet, row: int, col: int, previous: str, same_vendor: bool) -> str:
    """Value of a group column for one row.

    A typed value wins. A cell inside a merged block takes the block's value
    (a blank merged block really means "none"). Otherwise the value above is
    carried down, but only while the vendor has not changed.
    """
    value = sheet.cell(row, col)
    if as_text(value).strip():
        return _clean(value)                      # "-" becomes blank and stops the fill-down
    anchor = sheet.merged_anchor(row, col)
    if anchor is not None:
        return _clean(sheet.cell(*anchor))
    return previous if same_vendor else ""


def _dn_kind(text: str) -> str:
    if re.search(r"\bDN[-\s]?\d{4}[-\s]?\d+", text, re.IGNORECASE):
        return "DN"
    if re.search(r"(?<!\d)7100\d{6}(?!\d)", text):
        return "SAP"
    return ""


def read_sheet(sheet: Sheet, file_name: str) -> tuple[list[M.Line], list[str], str] | None:
    """Lines of one sheet, the headers the app didn't recognise, and the customer text."""
    header_row = find_header_row(sheet, [HEADERS["description"], HEADERS["qty"]])
    if header_row is None:
        return None
    header_cells = sheet.rows[header_row - 1]
    cols = map_headers(header_cells, HEADERS)
    if "description" not in cols or "qty" not in cols:
        return None
    known = set(cols.values())
    unknown_named = {c: as_text(v).strip() for c, v in enumerate(header_cells, start=1)
                     if as_text(v).strip() and c not in known}
    unnamed = [c for c in range(1, sheet.n_cols + 1)
               if c not in known and c not in unknown_named]

    def cell(row: int, name: str):
        return sheet.cell(row, cols[name]) if name in cols else None

    lines: list[M.Line] = []
    customers: Counter[str] = Counter()
    previous_vendor: str | None = None
    carried = {f: "" for f in GROUP_FIELDS}
    for r in range(header_row + 1, sheet.n_rows + 1):
        description = _clean(cell(r, "description"))
        article = _clean(cell(r, "article"))
        if not description and not article:
            continue
        if _TOTAL_ROW.match(description):
            continue
        vendor = _clean(cell(r, "vendor"))
        same_vendor = previous_vendor is not None and vendor == previous_vendor
        for f in GROUP_FIELDS:
            if f in cols:
                carried[f] = _group_value(sheet, r, cols[f], carried[f], same_vendor)
        previous_vendor = vendor

        qty = to_number(cell(r, "qty"))
        delivered = to_number(cell(r, "delivered"))
        value = to_number(cell(r, "value"))
        unit_price = to_number(cell(r, "unit_price"))
        if value is None and unit_price is not None and qty is not None:
            value = round(unit_price * qty, 2)
        notes = "; ".join(t for t in (_clean(sheet.cell(r, c)) for c in unnamed) if t)
        eta = to_date(cell(r, "eta"))
        if eta is None and re.search(r"\beta\b", notes, re.IGNORECASE):
            dated = find_dates(notes)
            eta = dated[0][2] if dated else None       # ETA notes without a year stay text
        dn = _clean(cell(r, "delivery_note"))
        customer = _clean(cell(r, "customer"))
        if customer:
            customers[customer] += 1
        lines.append(M.Line(
            excel_row=r, num=_clean(cell(r, "num")), article=article, description=description,
            unit=_clean(cell(r, "unit")), qty=qty, delivered=delivered, vendor=vendor,
            vendor_quote=_clean(cell(r, "vendor_quote")), quotation=carried["quotation"],
            sap_quotation=carried["sap_quotation"], sales_order=carried["sales_order"],
            pr_po=carried["pr_po"], client_po=_clean(cell(r, "client_po")),
            delivery_note=dn, delivery_note_kind=_dn_kind(dn),
            invoice=_clean(cell(r, "invoice")), value=value,
            dispatched=to_date(cell(r, "dispatched")), eta=eta, site=_clean(cell(r, "site")),
            remark=_clean(cell(r, "remarks")), notes=notes,
            extra={h: sheet.cell(r, c) for c, h in unknown_named.items()
                   if not is_blank(sheet.cell(r, c))},
            sheet=sheet.name, file=file_name))
    if not lines:
        return None
    customer = customers.most_common(1)[0][0] if customers else ""
    return lines, list(unknown_named.values()), customer


def read(workbook: Workbook, reading, cfg: dict, recognised: list[str]) -> str | None:
    if "register" in recognised:
        return None
    detail = M.DetailFile(path=str(workbook.path), name=workbook.name)
    for sheet in workbook.sheets:
        if re.search(r"correction|link", sheet.name, re.IGNORECASE):
            continue
        result = read_sheet(sheet, workbook.name)
        if result is None:
            continue
        lines, unknown, customer = result
        detail.lines.extend(lines)
        detail.sheets.append(sheet.name)
        detail.unknown_columns.extend(h for h in unknown if h not in detail.unknown_columns)
        detail.customer_name = detail.customer_name or customer
    if not detail.lines:
        return None
    codes: list[str] = []
    for text in [workbook.path.stem, detail.customer_name]:
        for code in _CODE.findall(text):
            if code not in codes:
                codes.append(code)
    detail.customer_codes = codes
    detail.sales_orders = sorted({ln.sales_order for ln in detail.lines if ln.sales_order})
    analyse(detail)
    reading.details.append(detail)
    sheets = "" if len(detail.sheets) == 1 else f" from {len(detail.sheets)} sheets"
    extra = (f"; columns kept as-is: {', '.join(detail.unknown_columns)}"
             if detail.unknown_columns else "")
    return f"detail file: {len(detail.lines)} lines{sheets}{extra}"
