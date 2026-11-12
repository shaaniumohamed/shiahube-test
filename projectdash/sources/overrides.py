"""Reads the optional ``Corrections`` and ``Links`` sheets.

They may live in the register workbook or in a workbook of their own (for
example the Corrections file downloaded from the app) anywhere in the data folder.
"""
from __future__ import annotations

import re

from ..excel import Workbook, find_header_row, map_headers
from ..textnorm import as_text

KIND = "corrections"

_CORRECTION_HEADERS = {
    "project": ["project", "project name"],
    "field": ["field", "what"],
    "value": ["value", "correct value", "new value"],
    "note": ["note", "notes", "reason", "comment"],
}
_LINK_HEADERS = {
    "file": ["file", "file name", "detail file", "filename"],
    "project": ["project", "project name"],
}


def read(workbook: Workbook, reading, cfg: dict, recognised: list[str]) -> str | None:
    from . import Correction, LinkRule

    found = []
    for sheet in workbook.sheets:
        if re.search(r"correction", sheet.name, re.IGNORECASE):
            row = find_header_row(sheet, [["project", "project name"], ["field"], ["value"]])
            if row is None:
                reading.problems.append(
                    f"'{workbook.name}', sheet '{sheet.name}': expected the headers "
                    "project | field | value | note in one row.")
                continue
            cols = map_headers(sheet.rows[row - 1], _CORRECTION_HEADERS)
            n = 0
            for r in range(row + 1, sheet.n_rows + 1):
                project = as_text(sheet.cell(r, cols["project"])).strip()
                field_name = as_text(sheet.cell(r, cols["field"])).strip()
                value = sheet.cell(r, cols["value"])
                if not project or not field_name or not as_text(value).strip():
                    continue                    # rows without a value are simply not used yet
                note = as_text(sheet.cell(r, cols["note"])).strip() if "note" in cols else ""
                reading.corrections.append(Correction(
                    project, field_name, value, note,
                    where=f"Corrections row {r} in '{workbook.name}'"))
                n += 1
            found.append(f"{n} correction{'s' if n != 1 else ''}")
        elif re.search(r"link", sheet.name, re.IGNORECASE):
            row = find_header_row(sheet, [_LINK_HEADERS["file"], _LINK_HEADERS["project"]])
            if row is None:
                reading.problems.append(
                    f"'{workbook.name}', sheet '{sheet.name}': expected the headers "
                    "file | project in one row.")
                continue
            cols = map_headers(sheet.rows[row - 1], _LINK_HEADERS)
            n = 0
            for r in range(row + 1, sheet.n_rows + 1):
                file_text = as_text(sheet.cell(r, cols["file"])).strip()
                project = as_text(sheet.cell(r, cols["project"])).strip()
                if file_text and project:
                    reading.links.append(LinkRule(
                        file_text, project, where=f"Links row {r} in '{workbook.name}'"))
                    n += 1
            found.append(f"{n} link{'s' if n != 1 else ''}")
    return ", ".join(found) if found else None
