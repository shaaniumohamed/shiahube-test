"""Rules for the line items of a project detail file.

Pure functions working on ``Line`` objects in file order: re-order detection,
line status, conflicts, progress and the findings shown under "Needs attention".
"""
from __future__ import annotations

import re
from collections import defaultdict

from . import model as M

_GI_MAKE = re.compile(r"(?:need\s+to\s+)?make\s+g\.?i\b", re.IGNORECASE)
_GI_REVERSE = re.compile(r"revers\w*\s+g\.?i\b", re.IGNORECASE)


def _same(a: float | None, b: float | None) -> bool:
    return a is not None and b is not None and abs(a - b) < 1e-6


def detect_reorders(lines: list[M.Line]) -> list[tuple[str, str]]:
    """Find items that were entered again on a later row instead of updated.

    In file order: a line with an undelivered balance, followed later by a line
    with the same article number whose quantity equals that balance, is a
    re-order. The earlier line then only counts for what it actually delivered.
    Returns the pairs as ("#" of the earlier line, "#" of the later line).
    """
    pairs: list[tuple[str, str]] = []
    taken: set[int] = set()
    for i, first in enumerate(lines):
        first.effective_qty = first.qty
        if not first.article or first.qty is None:
            continue
        balance = first.qty - (first.delivered or 0)
        if balance <= 1e-6:
            continue
        for j in range(i + 1, len(lines)):
            later = lines[j]
            if j in taken or later.article != first.article or not _same(later.qty, balance):
                continue
            taken.add(j)
            first.reordered_as = later.num or f"row {later.excel_row}"
            later.reorder_of = first.num or f"row {first.excel_row}"
            first.effective_qty = first.delivered or 0
            pairs.append((later.reorder_of, first.reordered_as))
            break
    return pairs


def set_status(line: M.Line) -> None:
    """Work out the status of one line. What the Remarks say beats the quantities."""
    remark = line.remark.lower()
    qty, eff, done = line.qty, line.effective_qty, line.delivered
    full_original = qty is not None and qty > 0 and done is not None and done >= qty - 1e-6
    full_effective = eff is not None and eff > 0 and done is not None and done >= eff - 1e-6
    line.conflict = False

    if line.reordered_as and not (done or 0) > 0:
        line.status = M.L_REORDERED               # nothing delivered here; the later row counts
        return
    if "cancel" in remark:
        line.status = M.L_CANCELLED
        return
    if "re-order" in remark or "reorder" in remark:
        line.status = M.L_REORDERED               # marked by hand as replaced by another row
        return
    if line.reordered_as and full_effective:
        line.status = M.L_DELIVERED               # delivered part done, the rest was re-ordered
        return
    if "out of stock" in remark or "no stock" in remark:
        line.status, line.conflict = M.L_OUT_OF_STOCK, full_original
    elif "pending" in remark or "not deliver" in remark or "awaiting" in remark:
        line.status, line.conflict = M.L_PENDING, full_original
    elif "deliver" in remark:
        short = done is not None and eff is not None and done < eff - 1e-6
        line.status = M.L_PARTIAL if short else M.L_DELIVERED
    elif full_effective:
        line.status = M.L_DELIVERED
    elif (done or 0) > 0:
        line.status = M.L_PARTIAL
    else:
        line.status = M.L_PENDING


def _delivered_share(line: M.Line) -> float:
    """How much of the line counts as delivered, 0–1."""
    if line.status == M.L_DELIVERED:
        return 1.0
    if line.conflict or not line.effective_qty:
        return 0.0
    return max(0.0, min(1.0, (line.delivered or 0) / line.effective_qty))


def progress(lines: list[M.Line]) -> M.Progress:
    """Progress by line count, by quantity (mixes units) and by value (if every line has one)."""
    active = [ln for ln in lines if ln.active]
    p = M.Progress(active_lines=len(active),
                   delivered_lines=sum(1 for ln in active if ln.status == M.L_DELIVERED))
    if not active:
        return p
    p.by_lines = round(100 * p.delivered_lines / len(active), 1)
    qty_total = sum(ln.effective_qty or 0 for ln in active)
    if qty_total > 0:
        p.by_qty = round(100 * sum((ln.effective_qty or 0) * _delivered_share(ln)
                                   for ln in active) / qty_total, 1)
    if all(ln.value is not None for ln in active) and sum(ln.value for ln in active) > 0:
        value_total = sum(ln.value for ln in active)
        p.by_value = round(100 * sum(ln.value * _delivered_share(ln) for ln in active)
                           / value_total, 1)
        p.basis = "value"
    else:
        p.basis = "line count"
    return p


def reused_articles(lines: list[M.Line]) -> list[str]:
    """Article numbers that appear with clearly different descriptions."""
    seen: dict[str, set[str]] = defaultdict(set)
    for ln in lines:
        if ln.article and ln.description:
            seen[ln.article].add(re.sub(r"\s+", " ", ln.description).strip().upper())
    return sorted(a for a, descriptions in seen.items() if len(descriptions) > 1)


def gi_counts(lines: list[M.Line]) -> tuple[int, int]:
    """Number of SAP goods-issue to-dos: (to make, to reverse)."""
    make = reverse = 0
    for ln in lines:
        text = " ".join([ln.notes, ln.remark, *(str(v) for v in ln.extra.values())])
        if _GI_REVERSE.search(text):
            reverse += 1
        elif _GI_MAKE.search(text):
            make += 1
    return make, reverse


def _numbers(nums: list[str], limit: int = 12) -> str:
    shown = ", ".join(f"#{n}" for n in nums[:limit])
    return shown + (f" and {len(nums) - limit} more" if len(nums) > limit else "")


def analyse(detail: M.DetailFile) -> M.DetailFile:
    """Apply every line rule to a detail file and write its findings."""
    lines = detail.lines
    detail.reorders = detect_reorders(lines)
    for ln in lines:
        set_status(ln)
    detail.progress = progress(lines)
    detail.conflict_lines = [ln.num or f"row {ln.excel_row}" for ln in lines if ln.conflict]
    detail.gi_to_make, detail.gi_to_reverse = gi_counts(lines)
    detail.reused_articles = reused_articles(lines)

    flags: list[M.Flag] = []
    if detail.conflict_lines:
        n = len(detail.conflict_lines)
        flags.append(M.Flag(
            "line_conflict",
            f"{n} line{'s are' if n > 1 else ' is'} marked pending or out of stock but "
            f"show{'' if n > 1 else 's'} full delivery ({_numbers(detail.conflict_lines)}). "
            "Counted as not delivered."))
    if detail.reorders:
        n = len(detail.reorders)
        pairs = ", ".join(f"#{a}→#{b}" for a, b in detail.reorders[:8])
        flags.append(M.Flag(
            "reorders", f"{n} re-order{'s' if n > 1 else ''} detected ({pairs}). "
                        "Each item is counted once."))
    if detail.gi_to_make or detail.gi_to_reverse:
        flags.append(M.Flag(
            "gi_notes", f"SAP goods-issue notes: {detail.gi_to_make} to make, "
                        f"{detail.gi_to_reverse} to reverse."))
    no_vendor = [ln.num or f"row {ln.excel_row}" for ln in lines if ln.open and not ln.vendor]
    if no_vendor:
        n = len(no_vendor)
        flags.append(M.Flag(
            "no_vendor", f"No vendor recorded for {n} open line{'s' if n > 1 else ''} "
                         f"({_numbers(no_vendor)})."))
    if detail.reused_articles:
        n = len(detail.reused_articles)
        flags.append(M.Flag(
            "article_reuse",
            f"{n} article number{'s are' if n > 1 else ' is'} used for different items "
            f"({', '.join(detail.reused_articles[:6])}{'…' if n > 6 else ''})."))
    if detail.progress.active_lines and detail.progress.basis != "value":
        flags.append(M.Flag(
            "no_values", "The lines have no values, so progress is measured by line count.",
            level="info"))
    detail.flags = flags
    return detail
