"""Deciding which project a detail file belongs to, and finding projects by name."""
from __future__ import annotations

import re

from . import model as M
from .textnorm import match_key

_DIGITS = re.compile(r"(?<!\d)(\d{6,})(?!\d)")


def find_projects(projects: list[M.Project], text: str) -> list[M.Project]:
    """Projects whose name matches the text.

    An exact name (ignoring case and spacing) wins; otherwise every project
    whose name contains the text is returned, so the caller can tell a unique
    match from an ambiguous one.
    """
    key = match_key(text)
    if not key:
        return []
    exact = [p for p in projects if match_key(p.name) == key]
    if exact:
        return exact
    return [p for p in projects if key in match_key(p.name)]


def project_codes(project: M.Project) -> set[str]:
    """Customer-style codes (6+ digits) written in the project name or client."""
    return set(_DIGITS.findall(f"{project.name} {project.client}"))


def link_details(details: list[M.DetailFile], projects: list[M.Project],
                 rules: list, saved: dict[str, str],
                 sales_orders: dict[str, set[str]]) -> list[str]:
    """Attach each detail file to a project. Returns plain-English problems.

    Order: the Links sheet, then a choice saved from the dropdown, then the
    customer code (when exactly one project carries it), then a shared Sales
    Order number. A file that matches nothing stays unlinked.
    """
    problems: list[str] = []
    by_key = {p.key: p for p in projects}

    def attach(detail: M.DetailFile, project: M.Project, reason: str) -> None:
        detail.linked_to, detail.link_reason = project.key, reason
        by_key[project.key].detail_files.append(detail)

    for detail in details:
        file_key = match_key(detail.name)
        linked = False

        for rule in rules:
            if match_key(rule.file_text) not in file_key:
                continue
            found = find_projects(projects, rule.project_text)
            if len(found) == 1:
                attach(detail, found[0], "Links sheet")
                linked = True
            elif not found:
                problems.append(f"{rule.where}: no project name contains '{rule.project_text}'.")
            else:
                problems.append(
                    f"{rule.where}: '{rule.project_text}' matches {len(found)} projects; "
                    "type more of the project name.")
            break
        if linked:
            continue

        chosen = saved.get(detail.name)
        if chosen:
            found = find_projects(projects, chosen)
            if len(found) == 1:
                attach(detail, found[0], "your choice")
                continue

        candidates = [p for p in projects if project_codes(p) & set(detail.customer_codes)]
        if len(candidates) == 1:
            code = sorted(project_codes(candidates[0]) & set(detail.customer_codes))[0]
            attach(detail, candidates[0], f"customer code {code}")
            continue
        pool = candidates or projects
        shared = [p for p in pool if sales_orders.get(p.key, set()) & set(detail.sales_orders)]
        if len(shared) == 1:
            attach(detail, shared[0], "Sales Order number")
            continue
        if len(candidates) > 1:
            detail.link_reason = (f"{len(candidates)} projects carry the customer code "
                                  f"{', '.join(detail.customer_codes)}")
    return problems
