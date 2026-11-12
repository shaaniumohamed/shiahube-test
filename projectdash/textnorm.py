"""Reading free text: separators, dates, amounts.

The notes in the Excel files are typed by hand, so every function here is
forgiving and none of them changes the original text.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

SEP = " | "

_MONTHS = ["january", "february", "march", "april", "may", "june", "july",
           "august", "september", "october", "november", "december"]

_BREAKS = re.compile(r"_x000[BbDdAa]_|[\n\r\x0b\x0c\t]+")
_HAS_BREAK = re.compile(r"_x000[BbDdAa]_|[\n\r\x0b\x0c]")
_MULTISPACE = re.compile(r" {2,}")
_SPACE = re.compile(r"[  ]+")

_DATE_DOTTED = re.compile(r"(?<![\d.])(\d{1,2})\.(\d{1,2})\.(\d{4})(?![\d])")
_DATE_NAMED = re.compile(
    r"(?<![\d])(\d{1,2})\s?(?:st|nd|rd|th)?[\s\-]+([A-Za-z]{3,9})\.?,?[\s\-]+(\d{4})(?!\d)",
    re.IGNORECASE)
_AMOUNT = re.compile(r"(?<![\d.,])(\d[\d,]{2,}\.\d{2})(?![\d])")


def as_text(value: Any) -> str:
    """Turn any cell into text ("" for an empty cell)."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (dt.datetime, dt.date)):
        d = value.date() if isinstance(value, dt.datetime) else value
        return d.strftime("%d.%m.%Y")
    return str(value)


def fragments(value: Any) -> list[str]:
    """Split a diary cell into its separate entries.

    Line breaks (also the ``_x000B_`` left behind by Excel) always separate
    entries. Runs of two or more spaces only count as a separator when the cell
    has no real line break at all, because people also type double spaces inside
    a sentence.
    """
    text = as_text(value)
    if not text.strip():
        return []
    has_break = bool(_HAS_BREAK.search(text))
    text = _BREAKS.sub("\n", text)
    if not has_break:
        text = _MULTISPACE.sub("\n", text)
    out = []
    for part in text.split("\n"):
        part = _SPACE.sub(" ", part).strip()
        if part:
            out.append(part)
    return out


def normalise(value: Any) -> str:
    """One-line version of a cell with " | " between its entries."""
    return SEP.join(fragments(value))


def match_key(value: Any) -> str:
    """Lower-case, single-spaced text used for "name contains" matching."""
    return re.sub(r"\s+", " ", as_text(value).replace(" ", " ")).strip().lower()


def _month_number(word: str) -> int | None:
    w = word.lower()
    if w == "sept":
        return 9
    if len(w) < 3:
        return None
    for i, name in enumerate(_MONTHS, start=1):
        if name.startswith(w):
            return i
    return None


def _make_date(y: int, m: int, d: int) -> dt.date | None:
    if not 1990 <= y <= 2100:
        return None
    try:
        return dt.date(y, m, d)
    except ValueError:
        return None


def find_dates(text: str) -> list[tuple[int, int, dt.date]]:
    """Every full date in the text as (start, end, date), in reading order.

    Recognised: ``18.12.2023``, ``10th June 2024``, ``22 July 2024``,
    ``31st Dec 2024``. Dates without a year are ignored on purpose.
    """
    found = []
    for m in _DATE_DOTTED.finditer(text):
        d = _make_date(int(m[3]), int(m[2]), int(m[1]))
        if d:
            found.append((m.start(), m.end(), d))
    for m in _DATE_NAMED.finditer(text):
        month = _month_number(m[2])
        if month:
            d = _make_date(int(m[3]), month, int(m[1]))
            if d:
                found.append((m.start(), m.end(), d))
    return sorted(found)


def parse_amount(text: str) -> float | None:
    try:
        return float(text.replace(",", ""))
    except (ValueError, AttributeError):
        return None


def find_amount(text: str) -> float | None:
    """The first money amount (digits with two decimals) in the text."""
    m = _AMOUNT.search(text)
    return parse_amount(m[1]) if m else None


def find_amounts(text: str) -> list[tuple[int, int, float]]:
    return [(m.start(), m.end(), parse_amount(m[1])) for m in _AMOUNT.finditer(text)]


def to_number(value: Any) -> float | None:
    """A cell as a number, rounded to cents to drop float artifacts."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    text = as_text(value).strip()
    if not text:
        return None
    cleaned = re.sub(r"(?i)mvr|rf\.?|usd|\s", "", text).replace(",", "")
    if cleaned.endswith("/-"):
        cleaned = cleaned[:-2]
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return None


def to_int(value: Any) -> int | None:
    """The first whole number in a cell ("75 days" -> 75)."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    m = re.search(r"\d+", as_text(value))
    return int(m[0]) if m else None


_EXCEL_EPOCH = dt.date(1899, 12, 30)


def to_date(value: Any) -> dt.date | None:
    """A cell as a date: real Excel dates, Excel serial numbers and typed dates."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, (int, float)):
        if 20000 <= value <= 80000:            # 1954 … 2119 as an Excel serial number
            return _EXCEL_EPOCH + dt.timedelta(days=int(value))
        return None
    text = as_text(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{5}(\.0+)?", text):
        return to_date(float(text))
    hits = find_dates(text)
    if hits:
        return hits[0][2]
    m = re.search(r"(?<!\d)(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})(?!\d)", text)
    if m:
        return _make_date(int(m[3]), int(m[2]), int(m[1]))
    m = re.search(r"(?<!\d)(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)", text)
    if m:
        return _make_date(int(m[1]), int(m[2]), int(m[3]))
    return None


def is_blank(value: Any) -> bool:
    """Empty cells and the "-" people type to mean "none"."""
    return as_text(value).strip() in ("", "-", "--", "–", "—", "n/a", "N/A", "nil", "NIL")
