"""Opening workbooks tolerantly.

A workbook is read once into plain lists (``Sheet``) so the rest of the code
never depends on the Excel library, and the source file is only ever opened
read-only.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import openpyxl

from .textnorm import as_text


@dataclass
class Sheet:
    name: str
    rows: list[list[Any]]                       # rows[r-1][c-1], like Excel
    merged: list[tuple[int, int, int, int]] = field(default_factory=list)  # r1, c1, r2, c2
    hidden_rows: set[int] = field(default_factory=set)

    @property
    def n_rows(self) -> int:
        return len(self.rows)

    @property
    def n_cols(self) -> int:
        return max((len(r) for r in self.rows), default=0)

    def cell(self, row: int, col: int) -> Any:
        if row < 1 or col < 1 or row > len(self.rows):
            return None
        r = self.rows[row - 1]
        return r[col - 1] if col <= len(r) else None

    def merged_anchor(self, row: int, col: int) -> tuple[int, int] | None:
        """Top-left cell of the merged block this cell belongs to, if any."""
        for r1, c1, r2, c2 in self.merged:
            if r1 <= row <= r2 and c1 <= col <= c2:
                return (r1, c1)
        return None


@dataclass
class Workbook:
    path: Path
    sheets: list[Sheet]

    @property
    def name(self) -> str:
        return self.path.name

    def sheet(self, name: str) -> Sheet | None:
        for s in self.sheets:
            if s.name == name:
                return s
        return None


class UnreadableWorkbook(Exception):
    """Raised with a plain-English reason when a file cannot be opened."""


def load_workbook(path: str | Path) -> Workbook:
    path = Path(path)
    try:
        # data_only=True gives the last value Excel calculated for formula cells.
        wb = openpyxl.load_workbook(path, data_only=True, read_only=False)
    except PermissionError as exc:
        raise UnreadableWorkbook(
            "the file is locked. Close it in Excel and refresh the page.") from exc
    except Exception as exc:  # noqa: BLE001 - any failure becomes a readable message
        raise UnreadableWorkbook(
            f"it could not be opened as an Excel workbook ({type(exc).__name__}).") from exc
    sheets = []
    for ws in wb.worksheets:
        if getattr(ws, "sheet_state", "visible") == "veryHidden":
            continue
        rows = [list(r) for r in ws.iter_rows(values_only=True)]
        # openpyxl starts at the first used row/column; pad so indexes match Excel.
        pad_rows, pad_cols = ws.min_row - 1, ws.min_column - 1
        if pad_cols:
            rows = [[None] * pad_cols + r for r in rows]
        if pad_rows:
            rows = [[] for _ in range(pad_rows)] + rows
        while rows and not any(v is not None and as_text(v).strip() for v in rows[-1]):
            rows.pop()
        merged = [(m.min_row, m.min_col, m.max_row, m.max_col) for m in ws.merged_cells.ranges]
        hidden = {r for r, d in ws.row_dimensions.items() if d.hidden}
        sheets.append(Sheet(ws.title, rows, merged, hidden))
    wb.close()
    return Workbook(path, sheets)


def header_key(value: Any) -> str:
    """A header reduced to lower-case words: "PR / PO" -> "pr po", "#" -> "#"."""
    text = as_text(value).strip().lower()
    if text in ("#", "no.", "no", "s/n", "sn", "sl", "sl.", "s.no", "s.no."):
        return "#"
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def _score(header: str, alias: str) -> float:
    if not header:
        return 0.0
    if header == alias:
        return 1.0
    ratio = difflib.SequenceMatcher(None, header, alias).ratio()
    if ratio >= 0.86 and len(alias) >= 5:          # typos such as "projct value mvr"
        return 0.9 * ratio
    if len(alias) >= 6 and (header.startswith(alias + " ") or header.endswith(" " + alias)):
        return 0.6                                  # "remarks / notes", "client name"
    return 0.0


def map_headers(header_cells: list[Any], spec: dict[str, list[str]]) -> dict[str, int]:
    """Match header cells to field names by name (never by position).

    ``spec`` maps a field name to the spellings it may have. Returns
    {field: column number}. Each column is used for at most one field and the
    best match wins, so "Status" and "Delivery status" don't steal each other.
    """
    keys = [header_key(v) for v in header_cells]
    candidates = []
    for field_name, aliases in spec.items():
        for col, key in enumerate(keys, start=1):
            best = max((_score(key, header_key(a)) for a in aliases), default=0.0)
            if best > 0:
                candidates.append((best, -col, field_name, col))
    candidates.sort(reverse=True)
    result: dict[str, int] = {}
    used: set[int] = set()
    for _score_value, _neg, field_name, col in candidates:
        if field_name in result or col in used:
            continue
        result[field_name] = col
        used.add(col)
    return result


def find_header_row(sheet: Sheet, required: list[list[str]], max_scan: int = 40) -> int | None:
    """First row (within the top ``max_scan``) that has a cell for every required header.

    ``required`` is a list of alias lists; each list must be matched by some cell.
    """
    wanted = [[header_key(a) for a in aliases] for aliases in required]
    for r in range(1, min(sheet.n_rows, max_scan) + 1):
        keys = [header_key(v) for v in sheet.rows[r - 1]]
        if all(any(_score(k, a) >= 0.75 for k in keys for a in aliases) for aliases in wanted):
            return r
    return None


def named_header_count(sheet: Sheet, row: int) -> int:
    return sum(1 for v in sheet.rows[row - 1] if as_text(v).strip())


def unnamed_columns_with_data(sheet: Sheet, header_row: int, after_col: int = 0) -> list[int]:
    """Columns that have no header but do hold data below the header row."""
    cols = []
    for c in range(after_col + 1, sheet.n_cols + 1):
        if as_text(sheet.cell(header_row, c)).strip():
            continue
        if any(as_text(sheet.cell(r, c)).strip() for r in range(header_row + 1, sheet.n_rows + 1)):
            cols.append(c)
    return cols


def list_workbooks(folder: str | Path) -> list[Path]:
    """Excel files in the folder (and one level of sub-folders), skipping lock files."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    found = []
    for pattern in ("*.xls*", "*/*.xls*"):
        for p in folder.glob(pattern):
            if p.name.startswith("~$") or p.name.startswith("."):
                continue
            if p.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
                found.append(p)
    return sorted(set(found), key=lambda p: p.name.lower())
