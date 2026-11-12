"""Rules for reading the free-text Status / REMARKS diaries of the register.

Every function is pure (text in, value out) so each rule can be tested alone.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

from . import model as M
from .textnorm import SEP, as_text, find_amount, find_dates, fragments

_SIGN = re.compile(r"\b(?:sign|singed)", re.IGNORECASE)
_DELIVERY_NOTE = re.compile(r"delivery\s*note", re.IGNORECASE)
_INVOICE_NO = re.compile(r"(?<!\d)(61\d{8}|92\d{7})(?!\d)")
_DAYS = re.compile(r"(\d{1,4})\s*(?:calendar\s+|working\s+)?days?\b", re.IGNORECASE)
_DURATION = re.compile(r"duration\W{0,4}(\d{1,4})\s*days?", re.IGNORECASE)
_RECEIVED = re.compile(r"payment\s+received|advance\s+payment|received\s+payment", re.IGNORECASE)
_BALANCE = re.compile(r"\bbalance\b", re.IGNORECASE)   # the typo "Balace" must not match
_SALES_ORDER = re.compile(r"(?<!\d)(31\d{8}|51\d{8})(?!\d)")


# ---------------------------------------------------------------- agreement date
def agreement_date(*cells: Any) -> tuple[dt.date, str] | None:
    """The date the agreement was signed, with the text it was read from.

    Looks at each entry that mentions "sign" (or the typo "singed") and takes
    the date closest to that word. Entries about a signed *delivery note* are
    skipped. If no entry holds both, a date within ~30 characters of the word
    in the neighbouring text is accepted.
    """
    for cell in cells:
        for frag in fragments(cell):
            if _DELIVERY_NOTE.search(frag):
                continue
            words = list(_SIGN.finditer(frag))
            dates = find_dates(frag)
            if not words or not dates:
                continue
            best = min(
                ((min(abs(s - w.start()), abs(e - w.start()), abs(s - w.end())), d)
                 for w in words for s, e, d in dates),
                key=lambda x: x[0])
            return best[1], frag
    for cell in cells:                      # fallback: date on the neighbouring line
        text = SEP.join(fragments(cell))
        for w in _SIGN.finditer(text):
            context = text[max(0, w.start() - 40): w.end() + 40]
            if _DELIVERY_NOTE.search(context):
                continue
            for s, e, d in find_dates(text):
                gap = s - w.end() if s >= w.end() else w.start() - e
                if 0 <= gap <= 30:
                    return d, text[max(0, min(s, w.start())): max(e, w.end())]
    return None


# ---------------------------------------------------------------- delivery period
def delivery_days(period_cell: Any, *note_cells: Any) -> tuple[int, str] | None:
    """Number of days allowed for delivery and where it was found."""
    text = as_text(period_cell).strip()
    if text:
        if isinstance(period_cell, (int, float)) and not isinstance(period_cell, bool):
            if 0 < period_cell < 2000:
                return int(period_cell), M.SRC_COLUMN
        m = _DAYS.search(text) or re.fullmatch(r"\s*(\d{1,4})\s*", text)
        if m:
            return int(m[1]), M.SRC_COLUMN
    for cell in note_cells:
        m = _DURATION.search(SEP.join(fragments(cell)))
        if m:
            return int(m[1]), M.SRC_NOTES
    return None


# ---------------------------------------------------------------- invoices
def find_invoices(*cells: Any) -> list[M.Invoice]:
    """Invoice numbers (10 digits starting 61, or 9 digits starting 92) and amounts.

    The amount is the first money figure within ~32 characters after the number.
    The same invoice mentioned twice is listed once.
    """
    found: dict[str, M.Invoice] = {}
    for cell in cells:
        text = SEP.join(fragments(cell))
        hits = list(_INVOICE_NO.finditer(text))
        for i, m in enumerate(hits):
            stop = min(m.end() + 32, hits[i + 1].start() if i + 1 < len(hits) else len(text))
            amount = find_amount(text[m.end():stop])
            inv = found.get(m[1])
            if inv is None:
                found[m[1]] = M.Invoice(m[1], amount)
            elif inv.amount is None and amount is not None:
                inv.amount = amount
    return list(found.values())


def invoice_total(invoices: list[M.Invoice]) -> float | None:
    """Sum of the invoices, or None when any amount is unknown."""
    if not invoices or any(i.amount is None for i in invoices):
        return None
    return round(sum(i.amount for i in invoices), 2)


# ---------------------------------------------------------------- payment
def payment_label_from_text(text: Any) -> str | None:
    """Translate the typed payment status into one of the fixed labels."""
    t = re.sub(r"\s+", " ", as_text(text)).strip().lower()
    if not t:
        return None
    if "not clear" in t or "unpaid" in t or "not paid" in t or "uncleared" in t:
        return M.P_UNPAID
    if "partial" in t or "partly" in t:
        return M.P_PARTLY
    if "need to dispatch" in t or "not sent" in t or "to be dispatched" in t:
        return M.P_NOT_SENT
    if "not invoice" in t or "not yet invoice" in t:
        return M.P_NOT_INVOICED
    if "complet" in t or "cleared" in t or "paid" in t:
        return M.P_PAID
    return None


def payment_label(payment_cell: Any, remarks_cell: Any, has_invoice: bool) -> tuple[str | None, str]:
    """Payment label and its source."""
    label = payment_label_from_text(payment_cell)
    if label:
        return label, M.SRC_COLUMN
    remarks = SEP.join(fragments(remarks_cell)).lower()
    if remarks.startswith("complet"):
        return M.P_PAID, M.SRC_NOTES
    if has_invoice:
        return M.P_NOT_RECORDED, M.SRC_CALC
    return None, M.SRC_NONE


def received_amount(*cells: Any) -> float | None:
    """Total of "Payment received - …" / "Advance payment … (…)" amounts."""
    total, any_found = 0.0, False
    for cell in cells:
        for frag in fragments(cell):
            m = _RECEIVED.search(frag)
            if not m:
                continue
            amount = find_amount(frag[m.end(): m.end() + 60])
            if amount is not None:
                total += amount
                any_found = True
    return round(total, 2) if any_found else None


def balance_amount(*cells: Any) -> float | None:
    """The figure after "Balance" (the last one mentioned wins)."""
    result = None
    for cell in cells:
        for frag in fragments(cell):
            m = _BALANCE.search(frag)
            if m:
                amount = find_amount(frag[m.end(): m.end() + 30])
                if amount is not None:
                    result = amount
    return result


def unpaid_amount(label: str | None, invoices: list[M.Invoice], received: float | None,
                  balance: float | None) -> tuple[float | None, str, str]:
    """Outstanding amount as (value, source, explanation). None means "Unclear"."""
    total = invoice_total(invoices)
    if label in (M.P_PAID, M.P_NOT_INVOICED, M.P_NOT_SENT):
        return 0.0, M.SRC_CALC, f"nothing is owed yet because the status is '{label}'"
    if label == M.P_UNPAID:
        if total is not None:
            return total, M.SRC_CALC, "sum of the invoice amounts"
        return None, M.SRC_NONE, "an invoice amount is missing"
    if label == M.P_PARTLY:
        if balance is not None:
            return balance, M.SRC_NOTES, "the 'Balance' figure in the notes"
        if total is not None and received is not None:
            if total - received >= 0:
                return round(total - received, 2), M.SRC_CALC, "invoices minus payments received"
            return None, M.SRC_NONE, "more was received than the invoices recorded"
        return None, M.SRC_NONE, "no balance, or no received amount, in the notes"
    return None, M.SRC_NONE, ""


def not_sent_amount(label: str | None, invoices: list[M.Invoice]) -> float | None:
    """Invoiced value that has not been sent to the client yet."""
    if label != M.P_NOT_SENT:
        return None
    return invoice_total(invoices)


# ---------------------------------------------------------------- delivery status
def delivery_status_from_text(*cells: Any) -> str:
    """Delivery status from the wording of the notes (last resort)."""
    t = SEP.join(SEP.join(fragments(c)) for c in cells).lower()

    def has(*words: str) -> bool:
        return any(w in t for w in words)

    if has("plan to", "held a meeting", "agreement signing", "proposal submitted") \
            and not has("deliver", "complet", "invoice"):
        return M.D_NOT_STARTED
    if has("ongoing", "on going", "on-going") and not has("deliver"):
        return M.D_IN_PROGRESS
    partial_hint = (has("1st lot", "2nd lot", "shortage")
                    or re.search(r"\beta\b", t) is not None
                    or "partial" in t.replace("partially cleared", ""))
    if partial_hint and has("deliver", "handover", "received"):
        return M.D_PARTLY
    if has("deliver", "complet"):
        return M.D_DELIVERED
    return M.D_UNKNOWN


def normalise_delivery_status(value: Any) -> str | None:
    """Accept the fixed names typed loosely ("partly", "Completed", "ongoing")."""
    t = as_text(value).strip().lower()
    if not t:
        return None
    if "not start" in t or "pipeline" in t or "not yet" in t:
        return M.D_NOT_STARTED
    if "part" in t:
        return M.D_PARTLY
    if "progress" in t or "ongoing" in t or "on going" in t:
        return M.D_IN_PROGRESS
    if "deliver" in t or "complet" in t or "done" in t:
        return M.D_DELIVERED
    return None


def normalise_payment_status(value: Any) -> str | None:
    t = as_text(value).strip().lower()
    for label in M.PAYMENT_LABELS:
        if t == label.lower():
            return label
    return payment_label_from_text(value)


# ---------------------------------------------------------------- timeline
def timeline(cells: dict[str, Any]) -> list[M.TimelineEntry]:
    """Dated entries from the notes, newest first.

    ``cells`` maps a column label to its cell. An entry that is only a date is
    joined with the entry after it.
    """
    entries: list[M.TimelineEntry] = []
    for where, cell in cells.items():
        frags: list[str] = []
        for frag in fragments(cell):
            parts = [p.strip() for p in frag.split(";")]
            dated = [p for p in parts if find_dates(p)]
            frags.extend(parts if len(dated) > 1 else [frag])
        i = 0
        while i < len(frags):
            frag = frags[i]
            dates = find_dates(frag)
            if dates:
                rest = (frag[:dates[0][0]] + frag[dates[0][1]:]).strip(" -:;,.()")
                if not rest and i + 1 < len(frags) and not find_dates(frags[i + 1]):
                    frag = f"{frag} {frags[i + 1]}"
                    i += 1
                entries.append(M.TimelineEntry(dates[0][2], frag, where))
            i += 1
    entries.sort(key=lambda e: e.date, reverse=True)
    return entries


def last_activity(entries: list[M.TimelineEntry], as_of: dt.date | None = None) -> dt.date | None:
    """Most recent dated entry (dates after the as-of date are plans, not activity)."""
    dates = [e.date for e in entries if as_of is None or e.date <= as_of]
    return max(dates) if dates else None


def suspicious_dates(entries: list[M.TimelineEntry], request_date: dt.date | None,
                     days: int = 30) -> list[dt.date]:
    """Dates in the notes that fall well before the request date (likely typos)."""
    if not request_date:
        return []
    limit = request_date - dt.timedelta(days=days)
    return sorted({e.date for e in entries if e.date < limit})


def sales_orders_in_text(*cells: Any) -> list[str]:
    out: list[str] = []
    for cell in cells:
        for m in _SALES_ORDER.finditer(as_text(cell)):
            if m[1] not in out:
                out.append(m[1])
    return out


def all_fragments(cells: dict[str, Any]) -> list[tuple[str, str]]:
    """Every entry of the notes as (column label, text)."""
    return [(where, frag) for where, cell in cells.items() for frag in fragments(cell)]

