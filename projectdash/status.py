"""Overall status of a project: Late, At risk, On track, …"""
from __future__ import annotations

import datetime as dt

from . import model as M


def project_status(delivery: str, agreement: dt.date | None, due: dt.date | None,
                   as_of: dt.date, progress_percent: float | None,
                   etas: list[dt.date], cfg: dict) -> tuple[str, list[str], int | None]:
    """Returns (status, reasons in plain English, days until due).

    Days until due is negative once the due date has passed.
    """
    risk = cfg.get("at_risk", {})
    within = int(risk.get("due_within_days", 14))
    behind = float(risk.get("progress_behind_points", 20))
    days_to_due = (due - as_of).days if due else None

    if delivery == M.D_NOT_STARTED and agreement is None:
        return M.S_PIPELINE, ["Not signed or started yet."], days_to_due
    if delivery == M.D_DELIVERED:
        return M.S_COMPLETE, ["Delivery is complete."], days_to_due
    if due is None:
        if delivery == M.D_UNKNOWN:
            return M.S_UNCLEAR, ["Delivery status is not known and there is no due date."], None
        return M.S_NO_DEADLINE, ["There is no due date, so lateness cannot be tracked."], None
    if as_of > due:
        late = (as_of - due).days
        return M.S_LATE, [f"{late} day{'s' if late != 1 else ''} past the due date."], days_to_due

    reasons: list[str] = []
    if days_to_due <= within:
        reasons.append(f"Due in {days_to_due} day{'s' if days_to_due != 1 else ''}.")
    if agreement and due > agreement and progress_percent is not None:
        time_used = 100 * (as_of - agreement).days / (due - agreement).days
        time_used = max(0.0, min(100.0, time_used))
        if time_used - progress_percent >= behind:
            reasons.append(f"{time_used:.0f}% of the time has gone but only "
                           f"{progress_percent:.0f}% is delivered.")
    late_etas = [e for e in etas if e > due]
    if late_etas:
        n = len(late_etas)
        reasons.append(f"{n} open line{'s have' if n > 1 else ' has'} an ETA after the due date "
                       f"(latest {max(late_etas).strftime('%d %b %Y')}).")
    if reasons:
        return M.S_AT_RISK, reasons, days_to_due
    return M.S_ON_TRACK, [f"Due in {days_to_due} days."], days_to_due
