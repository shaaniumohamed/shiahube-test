"""Portfolio: every project at a glance, worst first."""
from __future__ import annotations

import datetime as dt

import pandas as pd
import streamlit as st

import ui
from projectdash import model as M
from projectdash.export import table_rows

VIEWS = ["List", "Board", "Table"]


def _delivery_cell(p: M.Project, compact: bool = False) -> str:
    delivery = p.get("delivery_status")
    pr = p.progress
    if pr and pr.percent is not None:
        kind = "done" if p.status == M.S_COMPLETE else "late" if p.status == M.S_LATE else ""
        text = f"{pr.percent:.0f}% · {pr.delivered_lines} of {pr.active_lines} lines"
        return ui.meter(pr.percent, kind) + ("" if compact else f'<div class="small">{ui.esc(text)}</div>')
    if compact:
        return ""
    label = "Not known" if delivery == M.D_UNKNOWN else delivery
    note = " (assumed)" if p.source("delivery_status") == M.SRC_ASSUMED else ""
    return f'<span class="ink2" style="font-size:.86rem">{ui.esc(label)}{note}</span>'


def _due_cell(p: M.Project) -> str:
    due = p.get("due_date")
    if due is None:
        return '<span class="muted" style="font-size:.84rem">no due date</span>'
    days = p.days_to_due
    if p.status == M.S_COMPLETE:
        sub = "delivered"
    elif days < 0:
        sub = f"<b>{-days} day{'s' if days != -1 else ''} late</b>"
    elif days == 0:
        sub = "<b>due today</b>"
    else:
        sub = f"in {days} day{'s' if days != 1 else ''}"
    return f'<b>{ui.day(due)}</b><div class="small">{sub}</div>'


def _meta(p: M.Project, as_of: dt.date, has_new: bool) -> str:
    bits = [f"<span>{ui.esc(p.client or 'No client')}</span>"]
    if p.detail_files:
        bits.append('<span class="tag">detail file linked</span>')
    if p.is_new:
        bits.append('<span class="tag new">new project</span>')
    elif has_new:
        bits.append('<span class="tag new">new notes</span>')
    if p.last_activity:
        bits.append(f'<span class="muted">last activity {ui.esc(ui.ago(p.last_activity, as_of))}</span>')
    return "".join(bits)


def _count(p: M.Project) -> str:
    n = len(p.attention)
    if not n:
        return '<span class="count zero">–</span>'
    urgent = any(f.level == "urgent" for f in p.attention)
    return (f'<span class="count {"urgent" if urgent else ""}" '
            f'title="{n} item{"s" if n != 1 else ""} need attention">{n}</span>')


def _list(projects: list[M.Project], as_of: dt.date, fresh: set[str]) -> None:
    rows = []
    for p in projects:
        value = p.get("contract_value")
        rows.append(
            f'<a class="row" href="{ui.esc(ui.project_href(p))}" target="_self">'
            f'<div class="c-name"><div class="name" title="{ui.esc(p.name)}">{ui.esc(p.name)}</div>'
            f'<div class="meta">{_meta(p, as_of, p.key in fresh)}</div></div>'
            f'<div class="c-val val num" title="{ui.esc(ui.money(value))}">{ui.money(value, compact=True)}</div>'
            f'<div class="c-del">{_delivery_cell(p)}</div>'
            f'<div class="c-st">{ui.chip(p.status)}</div>'
            f'<div class="c-due due">{_due_cell(p)}</div>'
            f'<div class="c-fl r">{_count(p)}</div></a>')
    st.html('<div class="pd plist"><div class="hd"><div>Project</div><div class="r">Value</div>'
            '<div>Delivery</div><div>Status</div><div>Due</div><div class="r">Flags</div></div>'
            + "".join(rows) + "</div>")


def _board(projects: list[M.Project]) -> None:
    cols = []
    for status in M.STATUS_ORDER:
        mine = [p for p in projects if p.status == status]
        if not mine:
            continue
        cards = []
        for p in mine:
            days = p.days_to_due
            when = ""
            if p.get("due_date") and status not in (M.S_COMPLETE, M.S_PIPELINE):
                when = f"{-days}d late" if days < 0 else f"in {days}d"
            n = len(p.attention)
            cards.append(
                f'<a class="card" href="{ui.esc(ui.project_href(p))}" target="_self">'
                f'<div class="name">{ui.esc(p.name)}</div>'
                f'<div class="meta"><span>{ui.esc(p.client)}</span>'
                f'<span class="num">{ui.money(p.get("contract_value"), compact=True)}</span></div>'
                f'<div class="meta"><span>{ui.esc(when)}</span>'
                f'<span>{f"{n} flag" + ("s" if n != 1 else "") if n else ""}</span></div>'
                f'{_delivery_cell(p, compact=True)}</a>')
        cols.append(
            f'<div class="col"><h3><i style="background:{ui.STATUS_COLOR[status]}"></i>'
            f'{ui.esc(status)} <span>{len(mine)}</span></h3>{"".join(cards)}</div>')
    st.html(f'<div class="pd board">{"".join(cols)}</div>')


def _table(pf: M.Portfolio, projects: list[M.Project]) -> None:
    keys = {p.key for p in projects}
    df = pd.DataFrame([r for r in table_rows(pf) if r["key"] in keys])
    if df.empty:
        return
    shown = df.drop(columns=["key"])
    st.caption("Click the box at the start of a row to open that project. "
               "Click a column name to sort. Everything from the master list is here.")
    event = st.dataframe(
        shown, hide_index=True, on_select="rerun", selection_mode="single-row",
        key="portfolio_table", height=min(720, 38 * (len(shown) + 1) + 4),
        column_config={
            "Project": st.column_config.TextColumn(width="large", pinned=True),
            "Delivered %": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.0f%%"),
            "Value": st.column_config.NumberColumn(format="accounting"),
            "Invoiced": st.column_config.NumberColumn(format="accounting"),
            "Unpaid": st.column_config.NumberColumn(format="accounting"),
            "Agreement date": st.column_config.DateColumn(format="DD MMM YYYY"),
            "Due date": st.column_config.DateColumn(format="DD MMM YYYY"),
            "Request date": st.column_config.DateColumn(format="DD MMM YYYY"),
            "Last activity": st.column_config.DateColumn(format="DD MMM YYYY"),
            "Status notes": st.column_config.TextColumn(width="large"),
            "Remarks": st.column_config.TextColumn(width="large"),
        })
    st.download_button("Download this table (CSV)", shown.to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"projects-{pf.as_of.isoformat()}.csv", mime="text/csv",
                       icon=":material/download:")
    selected = event.selection.rows if event and event.selection else []
    if selected:
        key = df.iloc[selected[0]]["key"]
        params = {"p": key}
        if st.session_state.get("asof") != st.session_state.get("_asof_default"):
            params["asof"] = st.session_state["asof"].isoformat()
        st.session_state.pop("portfolio_table", None)
        st.switch_page(next(p for p in st.session_state["_pages"] if p.url_path == "project"),
                       query_params=params)


def _unlinked(pf: M.Portfolio, state) -> None:
    names = [p.name for p in sorted(pf.projects, key=lambda p: p.name.lower())]
    for detail in pf.unlinked:
        with st.container(border=True):
            why = f" ({detail.link_reason})" if detail.link_reason else ""
            st.markdown(
                f":material/link_off: **{detail.name}** is not linked to a project{why}. "
                f"It has {len(detail.lines)} lines. Choose its project once and the app remembers.")
            left, right = st.columns([4, 1], vertical_alignment="bottom")
            choice = left.selectbox("Project", names, index=None, placeholder="Choose the project…",
                                    key=f"link_{detail.name}", label_visibility="collapsed")
            if right.button("Link", key=f"linkbtn_{detail.name}", type="primary",
                            disabled=choice is None, width="stretch"):
                state.save_link(detail.name, choice)
                st.cache_data.clear()
                st.rerun()


def render() -> None:
    c = ui.ctx()
    pf, cfg, as_of = c["pf"], c["cfg"], c["as_of"]
    projects = pf.projects
    signed = [p for p in projects if p.signed]
    ui.head("Portfolio", f"As of <b>{ui.day(as_of)}</b> · {len(projects)} projects")

    if pf.is_sample:
        ui.banner("<b>These are made-up sample projects.</b> Put your own Excel files in the "
                  "<code>data</code> folder and press <i>Refresh files</i> to see your projects.")
    if not projects:
        ui.empty("No projects found yet. Put the register workbook (the one with a 'Project name' "
                 "column) in the data folder, then press Refresh files.")
        if pf.problems:
            ui.flags([M.Flag("problem", t) for t in pf.problems])
        return
    if pf.problems:
        n = len(pf.problems)
        ui.banner(f"{n} thing{'s' if n != 1 else ''} in the files could not be used. "
                  f'<a href="{ui.esc(ui.href("missing-info"))}" target="_self" '
                  'style="color:#1c5cab;text-decoration:underline">See Missing info</a>.', warn=True)

    # ---- summary tiles
    late = [p for p in projects if p.status == M.S_LATE]
    risk = [p for p in projects if p.status == M.S_AT_RISK]
    unclear = [p for p in projects if p.get("delivery_status") == M.D_UNKNOWN]
    owed = [p for p in projects if p.get("payment_status") in (M.P_UNPAID, M.P_PARTLY)]
    unpaid = sum(p.get("unpaid") or 0 for p in owed)
    unclear_money = sum(1 for p in owed if p.get("unpaid") is None)
    not_sent = sum(p.not_sent or 0 for p in projects)
    money_sub = []
    if unclear_money:
        money_sub.append(f"{unclear_money} more unclear")
    if not_sent:
        money_sub.append(f"{ui.money(not_sent, compact=True)} invoiced, not sent")
    ui.tiles([
        {"label": "Projects", "value": len(projects),
         "sub": f"{len(signed)} signed · {len(projects) - len(signed)} in pipeline"},
        {"label": "Late or at risk", "value": len(late) + len(risk),
         "sub": f"{len(late)} late · {len(risk)} at risk",
         "tone": "alert" if late else "warn" if risk else ""},
        {"label": "Delivery unclear", "value": len(unclear),
         "sub": "status not stated anywhere" if unclear else "every project has a status"},
        {"label": "Unpaid (known)", "value": ui.money(unpaid, compact=True),
         "unit": cfg.get("currency", ""), "title": ui.money(unpaid),
         "sub": " · ".join(money_sub) or f"across {len(owed)} projects"},
    ])
    counts = {s: sum(1 for p in projects if p.status == s) for s in M.STATUS_ORDER}
    segs = "".join(f'<span style="flex:{n};background:{ui.STATUS_COLOR[s]}" title="{s}: {n}"></span>'
                   for s, n in counts.items() if n)
    legend = "".join(f'<span><i style="background:{ui.STATUS_COLOR[s]}"></i>{s} <b>{n}</b></span>'
                     for s, n in counts.items() if n)
    st.html(f'<div class="pd"><div class="share" role="img" aria-label="Projects by status">{segs}</div>'
            f'<div class="legend">{legend}</div></div>')

    # ---- coming up
    horizon = int(cfg.get("upcoming_days", 30))
    soon = sorted((p for p in projects if p.days_to_due is not None and 0 <= p.days_to_due <= horizon
                   and p.status not in (M.S_COMPLETE, M.S_PIPELINE)), key=lambda p: p.days_to_due)
    if soon:
        ui.h2("Coming up", f"due in the next {horizon} days")
        st.html('<div class="pd upnext">' + "".join(
            f'<a href="{ui.esc(ui.project_href(p))}" target="_self"><b>{ui.esc(p.name[:48])}</b>'
            f'<span>{ui.day(p.get("due_date"))} · in {p.days_to_due} day{"s" if p.days_to_due != 1 else ""}</span></a>'
            for p in soon) + "</div>")

    if pf.unlinked:
        ui.h2("Detail files without a project", f"{len(pf.unlinked)}")
        _unlinked(pf, c["state"])

    # ---- the projects
    ui.h2("Projects")
    top = st.container(horizontal=True, vertical_alignment="bottom")
    query = top.text_input("Search", key="q", bind="query-params", icon=":material/search:",
                           placeholder="Project, client, invoice or Sales Order number",
                           label_visibility="collapsed", width=380)
    view = top.segmented_control("View", VIEWS, default="List", key="view", bind="query-params",
                                 label_visibility="collapsed", required=True)
    present = [s for s in M.STATUS_ORDER if counts[s]]
    chosen = st.pills("Status", present, selection_mode="multi", key="status", bind="query-params",
                      label_visibility="collapsed")

    shown = projects
    if chosen:
        shown = [p for p in shown if p.status in chosen]
    if query and query.strip():
        needle = query.strip().lower()
        shown = [p for p in shown if needle in " ".join([
            p.name, p.client, p.status_text, p.remarks_text, str(p.get("so_number") or ""),
            " ".join(i.number for i in p.invoices)]).lower()]
    if not shown:
        ui.empty("No project matches the search and filters.")
        return
    if len(shown) != len(projects):
        st.caption(f"Showing {len(shown)} of {len(projects)} projects.")
    if view == "Board":
        _board(shown)
    elif view == "Table":
        _table(pf, shown)
    else:
        _list(shown, as_of, {n.project_key for n in pf.new_notes})
