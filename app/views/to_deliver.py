"""To deliver: every open line across all linked detail files."""
from __future__ import annotations

from collections import defaultdict

import streamlit as st

import ui
from projectdash import model as M


def render() -> None:
    c = ui.ctx()
    pf = c["pf"]
    ui.head("To deliver", "Lines that are still pending, partly delivered or out of stock, "
                          "from every linked detail file.")
    pairs = [(p, ln) for p in pf.projects for ln in p.lines if ln.open]
    with_files = [p for p in pf.projects if p.detail_files]
    if not with_files:
        ui.empty("No detail file is linked to a project yet, so there are no line items to show.")
        return

    gi_make = sum(d.gi_to_make for p in with_files for d in p.detail_files)
    gi_reverse = sum(d.gi_to_reverse for p in with_files for d in p.detail_files)
    conflicts = sum(1 for _p, ln in pairs if ln.conflict)
    ui.tiles([
        {"label": "Open lines", "value": len(pairs),
         "sub": f"in {len({p.key for p, _ in pairs})} of {len(with_files)} projects with a detail file"},
        {"label": "Out of stock", "value": sum(1 for _p, ln in pairs if ln.status == M.L_OUT_OF_STOCK),
         "sub": "not yet re-ordered"},
        {"label": "Check these", "value": conflicts,
         "sub": "marked pending but quantities show delivered",
         "tone": "warn" if conflicts else ""},
        {"label": "SAP goods issue to-dos", "value": gi_make + gi_reverse,
         "sub": f"{gi_make} to make · {gi_reverse} to reverse"},
    ])
    without = [p for p in pf.projects if not p.detail_files and p.status not in
               (M.S_COMPLETE, M.S_PIPELINE)]
    if without:
        st.caption(f"{len(without)} open project{'s have' if len(without) != 1 else ' has'} no "
                   "detail file yet, so their items are not listed here: "
                   + ", ".join(p.name[:40] for p in without[:6]) + ("…" if len(without) > 6 else ""))
    if not pairs:
        ui.empty("Nothing is open. Every line in the linked detail files is delivered.")
        return

    top = st.container(horizontal=True, vertical_alignment="bottom")
    group_by = top.segmented_control("Group by", ["Project", "Vendor", "Status"], default="Project",
                                     key="deliver_group", required=True)
    needle = (top.text_input("Find", key="deliver_find", placeholder="Find an item, vendor or number",
                             icon=":material/search:", width=320, label_visibility="collapsed")
              or "").strip().lower()
    if needle:
        pairs = [(p, ln) for p, ln in pairs if needle in " ".join(
            [p.name, ln.num, ln.article, ln.description, ln.vendor, ln.delivery_note, ln.pr_po,
             ln.notes, ln.remark]).lower()]
    groups: dict[str, list] = defaultdict(list)
    for p, ln in pairs:
        key = p.name if group_by == "Project" else (ln.vendor or "No vendor recorded") \
            if group_by == "Vendor" else ln.status
        groups[key].append((p, ln))
    for name, items in sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0].lower())):
        project = items[0][0]
        link = (f' · <a class="lnk" style="color:#1c5cab" href="{ui.esc(ui.project_href(project))}" '
                f'target="_self">open project</a>') if group_by == "Project" else ""
        st.html(f'<div class="pd"><h2>{ui.esc(name)}<small>{len(items)} open line'
                f'{"s" if len(items) != 1 else ""}{link}</small></h2></div>')
        rows = []
        for p, ln in items:
            sub = [ui.esc(" · ".join(b for b in [
                ln.unit, f"article {ln.article}" if ln.article else "",
                (ln.vendor or "no vendor") if group_by != "Vendor" else "", ln.site] if b))]
            if group_by != "Project":
                sub.append(f'<a class="lnk" href="{ui.esc(ui.project_href(p))}" target="_self">'
                           f'{ui.esc(p.name[:70])}</a>')
            if ln.notes:
                sub.append(f"<b>{ui.esc(ln.notes)}</b>")
            if ln.reorder_of:
                sub.append(f"re-order of line #{ui.esc(ln.reorder_of)}")
            if ln.conflict:
                sub.append("marked not delivered, but the quantities show full delivery")
            eta = ui.day(ln.eta) if ln.eta else '<span class="muted">—</span>'
            if ln.eta and p.get("due_date") and ln.eta > p.get("due_date"):
                eta += '<div class="sub"><b>after the due date</b></div>'
            balance = ln.qty - (ln.delivered or 0) if ln.qty is not None and not ln.conflict else ln.qty
            rows.append([
                f'<span class="num">{ui.esc(ln.num)}</span>',
                ui.esc(ln.description) + "".join(f'<div class="sub">{s}</div>' for s in sub if s),
                ui.qty(balance), f"{ui.qty(ln.delivered or 0)} / {ui.qty(ln.qty)}",
                ui.line_chip(ln.status), eta,
                ui.esc(ln.pr_po) or '<span class="muted">—</span>'])
        ui.table(["#", "Item", "Still to deliver", "Delivered / Qty", "Status", "ETA", "PR / PO"],
                 rows, right={2, 3})
