"""What changed since the previous version of a file.

Each time a file's modified time changes, the notes of every project are
remembered. Comparing with the version before shows which lines are new,
without anyone having to re-read every cell.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from .textnorm import match_key


def fingerprint(projects: list) -> dict[str, list[str]]:
    """Notes of each project as {project name key: [entries]}."""
    from .notes import all_fragments

    result: dict[str, list[str]] = {}
    for p in projects:
        cells = {"Status": p.status_text, "Remarks": p.remarks_text, "Payment": p.payment_text}
        result.setdefault(match_key(p.name), []).extend(text for _where, text in all_fragments(cells))
    return result


def roll(stored: dict[str, Any], mtime: float, content: Any, today: dt.date) -> dict[str, Any]:
    """Advance a stored {"current", "previous"} pair when the file has changed."""
    current = stored.get("current")
    if current is None:
        return {"current": {"mtime": mtime, "seen": today.isoformat(), "content": content},
                "previous": None}
    if abs(float(current.get("mtime", 0)) - mtime) < 1e-6:
        return stored
    return {"current": {"mtime": mtime, "seen": today.isoformat(), "content": content},
            "previous": current}


def new_entries(previous: dict[str, list[str]] | None,
                current: dict[str, list[str]]) -> tuple[dict[str, list[str]], set[str]]:
    """Returns ({project key: entries not in the previous version}, new project keys)."""
    if previous is None:
        return {}, set()
    added: dict[str, list[str]] = {}
    new_projects: set[str] = set()
    for key, entries in current.items():
        if key not in previous:
            new_projects.add(key)
            continue
        before = {match_key(e) for e in previous[key]}
        fresh = [e for e in entries if match_key(e) not in before]
        if fresh:
            added[key] = fresh
    return added, new_projects
