"""Sources: one small reader per kind of file.

Each source looks at an opened workbook and adds whatever it recognises to a
``Reading``. To teach the app a new kind of file later (purchase orders,
shipments, an SAP export…), add a module with a ``read(workbook, reading, cfg)``
function and list it in ``SOURCES`` below. Nothing else has to change.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import model as M
from ..excel import UnreadableWorkbook, Workbook, list_workbooks, load_workbook


@dataclass
class RegisterRow:
    row: int
    cells: dict[str, Any]              # by field name (name, client, value, status, …)
    raw: dict[str, Any]                # by the header text exactly as typed
    payment_cell: Any = None
    hidden: bool = False


@dataclass
class RegisterTable:
    file: str
    sheet: str
    header_row: int
    columns: dict[str, int]
    rows: list[RegisterRow] = field(default_factory=list)
    mtime: float = 0.0


@dataclass
class Correction:
    project: str
    field: str
    value: Any
    note: str = ""
    where: str = ""                    # "Corrections row 3 in <file>"


@dataclass
class LinkRule:
    file_text: str
    project_text: str
    where: str = ""


@dataclass
class InvoiceRow:
    number: str
    amount: float | None = None
    project_text: str = ""
    customer: str = ""
    status: str = ""
    dispatched: dt.date | None = None


@dataclass
class Reading:
    """Everything recognised in the data folder."""
    folder: str
    registers: list[RegisterTable] = field(default_factory=list)
    details: list[M.DetailFile] = field(default_factory=list)
    corrections: list[Correction] = field(default_factory=list)
    links: list[LinkRule] = field(default_factory=list)
    invoice_rows: list[InvoiceRow] = field(default_factory=list)
    files: list[M.FileReport] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    mtimes: dict[str, float] = field(default_factory=dict)


from . import detail, invoice_sheet, overrides, register  # noqa: E402  (after the dataclasses)

# Order matters: the register claims its sheets first, a workbook that holds a
# register is not also read as a detail file.
SOURCES = [register, overrides, invoice_sheet, detail]


def read_folder(folder: str | Path, cfg: dict | None = None) -> Reading:
    """Read every Excel file in the folder. Never raises for a bad file."""
    cfg = cfg or {}
    reading = Reading(str(folder))
    paths = list_workbooks(folder)
    if not Path(folder).is_dir():
        reading.problems.append(f"The data folder '{folder}' does not exist.")
    for path in paths:
        if path.suffix.lower() == ".xls":
            reading.files.append(M.FileReport(
                path.name, "skipped",
                "Old .xls format. Open it in Excel and use Save As → Excel Workbook (.xlsx)."))
            continue
        try:
            workbook: Workbook = load_workbook(path)
        except UnreadableWorkbook as exc:
            reading.files.append(M.FileReport(path.name, "problem", f"Not read: {exc}"))
            reading.problems.append(f"'{path.name}' was not read: {exc}")
            continue
        reading.mtimes[path.name] = path.stat().st_mtime
        recognised: list[str] = []
        kinds: list[str] = []
        for source in SOURCES:
            try:
                what = source.read(workbook, reading, cfg, recognised)
            except Exception as exc:  # noqa: BLE001 - one odd file must not stop the app
                reading.problems.append(
                    f"'{path.name}': the {source.KIND} reader hit something unexpected "
                    f"({type(exc).__name__}: {exc}).")
                continue
            if what:
                recognised.append(source.KIND)
                kinds.append(what)
        if kinds:
            reading.files.append(M.FileReport(path.name, recognised[0], "; ".join(kinds)))
        else:
            reading.files.append(M.FileReport(
                path.name, "skipped",
                "No table recognised (no 'Project name' header and no "
                "'Description' + 'Quantity' headers)."))
    return reading
