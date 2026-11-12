"""Updates: what is new in the notes and what has gone quiet."""
from __future__ import annotations

import datetime as dt

import streamlit as st

import ui
from projectdash import model as M


def render() -> None:
    c = ui.ctx()
    pf, cfg, as_of = c["pf"], c["cfg"], c["as_of"]
    ui.head("Updates", "New notes since the previous version of the master list, the latest dated "
                       "entries across all projects, and projects with no recent update.")
    by_key = {p.key: p for p in pf.projects}

    # ---- new since the previous version
    since = ""
    if pf.previous_version:
        since = f"compared with the version first seen on {ui.day(dt.date.fromisoformat(pf.previous_version))}"
    ui.h2("New since the previous version", since)
    new_projects = [p for p in pf.projects if p.is_new]
    if not pf.previous_version:
        ui.empty("The app has seen one version of the master list so far. When you save an updated "
                 "file into the data folder, the lines that are new will be listed here.")
    elif not pf.new_notes and not new_projects:
        ui.empty("Nothing new in the notes compared with the previous version.")
    else:
        rows = []
        for p in new_projects:
            rows.append([f'<a class="lnk" href="{ui.esc(ui.project_href(p))}" target="_self">'
                         f'{ui.esc(p.name)}</a><div class="sub">{ui.esc(p.client)}</div>',
                         '<span class="tag new">new project</span>', ""])
        for n in pf.new_notes:
            p = by_key[n.project_key]
            rows.append([f'<a class="lnk" href="{ui.esc(ui.project_href(p))}" target="_self">'
                         f'{ui.esc(p.name)}</a><div class="sub">{ui.esc(p.client)}</div>',
                         ui.esc(n.text), ui.day(n.date) if n.date else '<span class="muted">no date</span>'])
        ui.table(["Project", "New line in the notes", "Dated"], rows)

    # ---- latest dated entries
    ui.h2("Latest dated entries", "newest first, across all projects")
    past = [t.date for p in pf.projects for t in p.timeline if t.date <= as_of]
    newest_age = (as_of - max(past)).days if past else None
    options = {"30 days": 30, "90 days": 90, "1 year": 365, "Everything": None}
    # open on the shortest period that actually has something in it
    start = next((name for name, limit in options.items()
                  if limit is None or (newest_age is not None and newest_age <= limit)), "Everything")
    window = st.segmented_control("Period", list(options), default=start, key="updates_window",
                                  required=True, label_visibility="collapsed")
    days = options.get(window)
    entries = [(t, p) for p in pf.projects for t in p.timeline if t.date <= as_of
               and (days is None or (as_of - t.date).days <= days)]
    entries.sort(key=lambda x: x[0].date, reverse=True)
    if not entries:
        newest = max((t.date for p in pf.projects for t in p.timeline if t.date <= as_of), default=None)
        ui.empty("No dated entries in this period."
                 + (f" The most recent one is from {ui.day(newest)}." if newest else ""))
    else:
        rows = [[f'<span class="nw">{ui.day(t.date)}</span>',
                 f'<a class="lnk" href="{ui.esc(ui.project_href(p))}" target="_self">{ui.esc(p.name[:80])}</a>'
                 f'<div class="sub">{ui.esc(p.client)}</div>',
                 ui.esc(t.text) + (' <span class="tag new">new</span>' if t.is_new else "")]
                for t, p in entries[:150]]
        ui.table(["Date", "Project", "Entry"], rows)
        if len(entries) > 150:
            st.caption(f"Showing the newest 150 of {len(entries)} entries.")

    # ---- gone quiet
    limit = int(cfg.get("stale_update_days", 30))
    quiet = [p for p in pf.projects
             if not (p.status == M.S_COMPLETE and p.get("payment_status") == M.P_PAID)
             and (p.last_activity is None or (as_of - p.last_activity).days > limit)]
    quiet.sort(key=lambda p: p.last_activity or dt.date.min)
    ui.h2("No recent update", f"open or unpaid projects with nothing dated in the last {limit} days")
    if not quiet:
        ui.empty("Every open project has a recent dated note.")
        return
    rows = [[f'<a class="lnk" href="{ui.esc(ui.project_href(p))}" target="_self">{ui.esc(p.name[:80])}</a>'
             f'<div class="sub">{ui.esc(p.client)}</div>', ui.chip(p.status),
             ui.day(p.last_activity) if p.last_activity else '<span class="muted">no dated notes</span>',
             ui.esc(ui.ago(p.last_activity, as_of)) if p.last_activity else ""]
            for p in quiet]
    ui.table(["Project", "Status", "Last dated note", ""], rows)
