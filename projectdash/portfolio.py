"""The one entry point: read the folder and return a ``Portfolio``."""
from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any

from . import model as M
from . import snapshot
from .attention import project_flags
from .config import as_of_date
from .excel import list_workbooks
from .linking import find_projects, link_details
from .resolve import (base_project, correction_field, correction_value, register_sales_orders,
                      resolve_project)
from .sources import read_folder
from .state import StateStore
from .textnorm import match_key

_ORDER = {s: i for i, s in enumerate(M.STATUS_ORDER)}


def folder_stamp(folder: str | Path) -> tuple:
    """Changes whenever a file in the folder is added, removed or saved."""
    return tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in list_workbooks(folder))


def choose_folder(cfg: dict[str, Any]) -> tuple[str, bool]:
    """The data folder, or the made-up sample folder when the data folder is empty."""
    if list_workbooks(cfg["data_folder"]):
        return cfg["data_folder"], False
    if list_workbooks(cfg.get("sample_folder", "")):
        return cfg["sample_folder"], True
    return cfg["data_folder"], False


def _sort_key(p: M.Project):
    urgency = p.days_to_due if p.days_to_due is not None else 10 ** 6
    return (_ORDER.get(p.status, 99), urgency, -(p.get("contract_value") or 0), p.row)


def load_portfolio(cfg: dict[str, Any], as_of: dt.date | None = None,
                   state: StateStore | None = None, folder: str | None = None,
                   today: dt.date | None = None) -> M.Portfolio:
    """Read every Excel file in the folder and work out the whole portfolio.

    ``as_of`` is the date lateness is measured from. ``state`` is where link
    choices and file snapshots are remembered (nothing is remembered without it).
    """
    is_sample = False
    if folder is None:
        folder, is_sample = choose_folder(cfg)
    as_of = as_of or as_of_date(cfg, is_sample)
    reading = read_folder(folder, cfg)
    portfolio = M.Portfolio(as_of=as_of, folder=str(folder), files=reading.files,
                            problems=list(reading.problems), is_sample=is_sample)
    if cfg.get("config_problem"):
        portfolio.problems.insert(0, cfg["config_problem"])

    # ---- projects as typed
    rows: dict[str, Any] = {}
    sales_orders: dict[str, set[str]] = {}
    several = len(reading.registers) > 1
    for index, table in enumerate(reading.registers, start=1):
        for row in table.rows:
            key = f"{index}r{row.row}" if several else f"r{row.row}"
            portfolio.projects.append(base_project(row, table, key))
            rows[key] = row
            sales_orders[key] = register_sales_orders(row)
    if not reading.registers and list_workbooks(folder):
        portfolio.problems.append(
            "No register was found: no sheet has a 'Project name' header.")

    # ---- detail files
    saved = state.links() if state else {}
    portfolio.problems += link_details(reading.details, portfolio.projects, reading.links,
                                       saved, sales_orders)
    portfolio.unlinked = [d for d in reading.details if d.linked_to is None]

    # ---- corrections
    per_project: dict[str, dict[str, tuple[Any, str]]] = {}
    for corr in reading.corrections:
        field = correction_field(corr.field)
        if field is None:
            portfolio.problems.append(
                f"{corr.where}: '{corr.field}' is not a field the app knows. "
                f"Use one of: {', '.join(M.CORRECTION_FIELDS)}.")
            continue
        found = find_projects(portfolio.projects, corr.project)
        if not found:
            portfolio.problems.append(
                f"{corr.where}: no project name contains '{corr.project}'.")
            continue
        if len(found) > 1:
            portfolio.problems.append(
                f"{corr.where}: '{corr.project}' matches {len(found)} projects; "
                "type more of the project name.")
            continue
        try:
            value = correction_value(field, corr.value)
        except ValueError as exc:
            portfolio.problems.append(f"{corr.where}: the value for {field} {exc}.")
            continue
        per_project.setdefault(found[0].key, {})[field] = (value, corr.note)

    # ---- resolve every project
    invoice_rows = {r.number: r for r in reading.invoice_rows}
    for p in portfolio.projects:
        resolve_project(p, rows[p.key], per_project.get(p.key, {}), invoice_rows, as_of, cfg)
        p.flags, p.missing = project_flags(p, as_of, cfg)
    used = {i.number for p in portfolio.projects for i in p.invoices}
    portfolio.unmatched_invoices = [
        M.UnmatchedInvoice(r.number, r.amount, r.project_text, r.customer, r.status, r.dispatched)
        for r in reading.invoice_rows if r.number not in used]

    # ---- what changed since the previous version of the files
    if state is not None:
        _apply_snapshots(portfolio, reading, state, today or dt.date.today())

    portfolio.projects.sort(key=_sort_key)
    return portfolio


def _apply_snapshots(portfolio: M.Portfolio, reading, state: StateStore, today: dt.date) -> None:
    stored = state.load("snapshots")
    changed = False

    for table in reading.registers:
        mine = [p for p in portfolio.projects if p.register_file == table.file]
        current = snapshot.fingerprint(mine)
        name = f"register::{table.file}"
        before = stored.get(name, {})
        after = snapshot.roll(before, table.mtime, current, today)
        if after is not before:
            stored[name], changed = after, True
        previous = after.get("previous")
        if not previous:
            continue
        portfolio.previous_version = previous.get("seen", "")
        added, new_projects = snapshot.new_entries(previous.get("content"), current)
        for p in mine:
            key = match_key(p.name)
            p.is_new = key in new_projects
            fresh = added.get(key, [])
            for text in fresh:
                dated = next((t for t in p.timeline if text in t.text), None)
                if dated:
                    dated.is_new = True
                portfolio.new_notes.append(M.NewNote(
                    p.key, p.name, text, "", dated.date if dated else None))

    for detail in portfolio.detail_files:
        name = f"detail::{detail.name}"
        mtime = reading.mtimes.get(detail.name, 0.0)
        content = {"delivered": detail.progress.delivered_lines,
                   "active": detail.progress.active_lines}
        before = stored.get(name, {})
        after = snapshot.roll(before, mtime, content, today)
        if after is not before:
            stored[name], changed = after, True
        previous = after.get("previous")
        if previous and isinstance(previous.get("content"), dict):
            detail.delivered_change = (detail.progress.delivered_lines
                                       - int(previous["content"].get("delivered", 0)))
    if changed:
        state.save("snapshots", stored)
