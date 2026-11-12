"""Project page: everything the app knows about one project, with its sources."""
from __future__ import annotations

import streamlit as st

import ui
from projectdash import model as M
from projectdash.textnorm import as_text

LINE_FILTERS = ["All", "Open", "Delivered", "Re-ordered"]


def _value(p: M.Project, name: str) -> str:
    v = p.get(name)
    if v is None or v == "":
        return '<span class="muted">—</span>'
    if name in ("contract_value", "unpaid", "invoiced"):
        return f'<span class="num">{ui.money(v)}</span>'
    if name.endswith("_date"):
        return ui.day(v)
    if name == "delivery_days":
        return f"{v} days"
    return ui.esc(v)


def _what_the_app_read(p: M.Project) -> None:
    rows = []

    def add(label: str, name: str) -> None:
        s = p.values.get(name, M.Sourced())
        rows.append([ui.esc(label), _value(p, name), ui.source(s.source),
                     f'<span class="ink2">{ui.esc(s.note)}</span>'])

    add("Contract value", "contract_value")
    add("Request date", "request_date")
    add("Agreement signed", "agreement_date")
    add("Delivery period", "delivery_days")
    add("Due date", "due_date")
    add("Delivery status", "delivery_status")
    add("Payment status", "payment_status")
    add("Invoiced", "invoiced")
    received = (f'<span class="num">{ui.money(p.received)}</span>' if p.received is not None
                else '<span class="muted">—</span>')
    rows.append(["Payments received", received,
                 ui.source(M.SRC_NOTES if p.received is not None else M.SRC_NONE), ""])
    add("Unpaid", "unpaid")
    if p.not_sent:
        rows.append(["Invoiced, not yet sent", f'<span class="num">{ui.money(p.not_sent)}</span>',
                     ui.source(M.SRC_CALC), ""])
    add("Next action", "next_action")
    for label, name in (("Order type", "order_type"), ("PR number", "pr_number"),
                        ("PR date", "pr_date"), ("SO number", "so_number")):
        if p.get(name):
            add(label, name)
    ui.table(["What", "Value", "Source", "How"], rows)


def _invoices(p: M.Project) -> None:
    if not p.invoices:
        return
    ui.h2("Invoices", f"{len(p.invoices)}")
    rows = []
    for inv in p.invoices:
        amount = (f'{ui.money(inv.amount)}' if inv.amount is not None
                  else '<span class="muted">amount not recorded</span>')
        rows.append([f'<span class="num">{ui.esc(inv.number)}</span>', amount,
                     ui.source(inv.amount_source if inv.amount is not None else M.SRC_NONE),
                     ui.day(inv.sheet_dispatched) if inv.sheet_dispatched else '<span class="muted">—</span>',
                     ui.esc(inv.sheet_status) or '<span class="muted">not in the INVOICE sheet</span>'])
    ui.table(["Invoice", "Amount", "Amount from", "Dispatched (INVOICE sheet)",
              "Payment status (INVOICE sheet)"], rows, right={1})


def _line_row(ln: M.Line) -> list[str]:
    sub = []
    bits = [b for b in [ln.unit, ln.vendor or ("no vendor" if ln.open else ""),
                        f"article {ln.article}" if ln.article else "", ln.site] if b]
    if bits:
        sub.append(ui.esc(" · ".join(bits)))
    if ln.remark:
        sub.append(f'remark: “{ui.esc(ln.remark)}”')
    if ln.notes:
        sub.append(f'<b>{ui.esc(ln.notes)}</b>')
    if ln.reordered_as:
        sub.append(f"re-ordered as line #{ui.esc(ln.reordered_as)}")
    if ln.reorder_of:
        sub.append(f"re-order of line #{ui.esc(ln.reorder_of)}")
    if ln.conflict:
        sub.append("marked not delivered, but the quantities show full delivery")
    if ln.eta:
        sub.append(f"ETA {ui.day(ln.eta)}")
    for header, value in ln.extra.items():
        sub.append(f"{ui.esc(header)}: {ui.esc(as_text(value))}")
    item = f'{ui.esc(ln.description)}' + "".join(f'<div class="sub">{s}</div>' for s in sub)
    done = ui.qty(ln.delivered if ln.delivered is not None else 0)
    dn = ui.esc(ln.delivery_note) if ln.delivery_note else '<span class="muted">—</span>'
    if ln.delivery_note_kind == "SAP":
        dn += '<div class="sub">SAP</div>'
    refs = " · ".join(ui.esc(f"{k} {v}") for k, v in (("PO", ln.pr_po), ("SO", ln.sales_order)) if v)
    return [f'<span class="num">{ui.esc(ln.num)}</span>', item,
            f'{done} / {ui.qty(ln.qty)}', ui.line_chip(ln.status),
            dn + (f'<div class="sub">{refs}</div>' if refs else "")]


def _lines(p: M.Project) -> None:
    lines = p.lines
    pr = p.progress
    ui.h2("Line items", f"{len(lines)} rows in {len(p.detail_files)} file"
                        f"{'s' if len(p.detail_files) != 1 else ''}")
    for d in p.detail_files:
        change = ""
        if d.delivered_change:
            change = f" · {d.delivered_change:+d} delivered since the previous version of the file"
        st.caption(f":material/description: {d.name} · linked by {d.link_reason}{change}")
    if pr and pr.active_lines:
        parts = [f"**{pr.delivered_lines} of {pr.active_lines}** active lines delivered "
                 f"({pr.by_lines:.0f}%)"]
        if pr.by_qty is not None:
            parts.append(f"{pr.by_qty:.0f}% by quantity (mixes units)")
        parts.append(f"{pr.by_value:.0f}% by value" if pr.by_value is not None
                     else "no line values, so progress is by line count")
        st.markdown(" · ".join(parts))
    counts = {
        "All": len(lines),
        "Open": sum(1 for ln in lines if ln.open),
        "Delivered": sum(1 for ln in lines if ln.status == M.L_DELIVERED),
        "Re-ordered": sum(1 for ln in lines if ln.reordered_as or ln.reorder_of),
    }
    top = st.container(horizontal=True, vertical_alignment="bottom")
    choice = top.segmented_control("Show", LINE_FILTERS, default="Open" if counts["Open"] else "All",
                                   key=f"lines_{p.key}", required=True, label_visibility="collapsed",
                                   format_func=lambda f: f"{f} · {counts[f]}")
    needle = (top.text_input("Find", key=f"find_{p.key}", placeholder="Find an item, vendor or number",
                             label_visibility="collapsed", icon=":material/search:", width=320)
              or "").strip().lower()
    if choice == "Open":
        lines = [ln for ln in lines if ln.open]
    elif choice == "Delivered":
        lines = [ln for ln in lines if ln.status == M.L_DELIVERED]
    elif choice == "Re-ordered":
        lines = [ln for ln in lines if ln.reordered_as or ln.reorder_of]
    if needle:
        lines = [ln for ln in lines if needle in " ".join([
            ln.num, ln.article, ln.description, ln.vendor, ln.delivery_note, ln.pr_po,
            ln.sales_order, ln.remark, ln.notes]).lower()]
    if not lines:
        ui.empty("No lines match.")
        return
    ui.table(["#", "Item", "Delivered / Qty", "Status", "Delivery note"],
             [_line_row(ln) for ln in lines], right={2},
             row_classes=["dim" if not ln.active else "" for ln in lines])


def _timeline(p: M.Project) -> None:
    ui.h2("Timeline", "dated entries from the notes, newest first")
    if not p.timeline:
        ui.empty("The notes have no dated entries.")
    else:
        st.html('<div class="pd tl">' + "".join(
            f'<div class="e {"new" if t.is_new else ""}"><span class="d">{ui.day(t.date)}</span>'
            f'{ui.esc(t.text)}<span class="w">{ui.esc(t.where)}{" · new" if t.is_new else ""}</span></div>'
            for t in p.timeline) + "</div>")
    if st.toggle("Show original text", key=f"orig_{p.key}",
                 help="Exactly what is typed in the master list, untouched."):
        blocks = []
        for header, value in p.raw.items():
            blocks.append(f'<div class="orig-label">{ui.esc(header)}</div>'
                          f'<pre class="orig">{ui.esc(as_text(value))}</pre>')
        st.html(f'<div class="pd">{"".join(blocks)}</div>')
        st.caption(f"Row {p.row} of {p.register_file}")


def render() -> None:
    c = ui.ctx()
    pf, cfg, as_of = c["pf"], c["cfg"], c["as_of"]
    key = st.query_params.get("p") or st.session_state.get("_project")
    p = pf.project(key) if key else None
    if p is None:
        ui.head("Project", "Choose a project to open.")
        if not pf.projects:
            ui.empty("No projects found yet.")
            return
        choice = st.selectbox("Project", pf.projects, index=None, placeholder="Choose a project…",
                              format_func=lambda x: f"{x.name} ({x.client})",
                              label_visibility="collapsed")
        if choice:
            st.query_params["p"] = choice.key
            st.rerun()
        return
    st.session_state["_project"] = p.key
    if st.query_params.get("p") != p.key:
        st.query_params["p"] = p.key

    tags = "".join([
        ui.chip(p.status),
        f'<span class="chip ghost">{ui.esc(p.client)}</span>' if p.client else "",
        f'<span class="chip ghost">{ui.esc(p.get("order_type"))}</span>' if p.get("order_type") else "",
        '<span class="tag new">new project</span>' if p.is_new else "",
    ])
    reasons = ui.esc(" ".join(p.status_reasons))
    ui.head(p.name, f'<span style="display:inline-flex;gap:8px;flex-wrap:wrap;align-items:center;'
                    f'margin-top:6px">{tags}<span>{reasons}</span></span>',
            crumb=("All projects", ui.href("")))

    # ---- cards
    pr = p.progress
    delivery = p.get("delivery_status")
    if pr and pr.percent is not None:
        d_value, d_sub = f"{pr.percent:.0f}%", f"{pr.delivered_lines} of {pr.active_lines} lines · by {pr.basis}"
    else:
        d_value = "Not known" if delivery == M.D_UNKNOWN else delivery
        d_sub = p.source("delivery_status")
    due = p.get("due_date")
    if due is None:
        due_value, due_sub, tone = "No due date", "add a delivery period to track it", ""
    elif p.status == M.S_COMPLETE:
        due_value, due_sub, tone = ui.day(due), "delivered", ""
    elif p.days_to_due < 0:
        due_value, due_sub, tone = ui.day(due), f"{-p.days_to_due} days late", "alert"
    else:
        due_value, due_sub = ui.day(due), f"in {p.days_to_due} days"
        tone = "warn" if p.status == M.S_AT_RISK else ""
    unpaid = p.get("unpaid")
    pay = p.get("payment_status")
    if unpaid is not None:
        u_value, u_unit = ui.money(unpaid, compact=True), cfg.get("currency", "")
    else:
        u_value, u_unit = ("Unclear" if pay in (M.P_UNPAID, M.P_PARTLY, M.P_NOT_RECORDED) else "—"), ""
    ui.tiles([
        {"label": "Delivery", "value": d_value, "sub": d_sub},
        {"label": "Due date", "value": due_value, "sub": due_sub, "tone": tone},
        {"label": "Last activity", "value": ui.ago(p.last_activity, as_of).capitalize(),
         "sub": ui.day(p.last_activity) if p.last_activity else "nothing dated in the notes"},
        {"label": "Unpaid", "value": u_value, "unit": u_unit, "title": ui.money(unpaid),
         "sub": pay or "no payment status"},
    ])
    if p.get("next_action"):
        ui.banner(f"<b>Next action:</b> {ui.esc(p.get('next_action'))}")

    ui.h2("Needs attention", f"{len(p.attention)}")
    ui.flags(p.flags)

    ui.h2("What the app read", "every value with where it came from")
    _what_the_app_read(p)
    if p.missing:
        st.caption("Something wrong or missing? Add a row to a Corrections sheet "
                   "(project | field | value | note). The Missing info page has a ready-made file.")
    _invoices(p)
    if p.detail_files:
        _lines(p)
    else:
        ui.h2("Line items")
        ui.empty("No detail file is linked to this project yet. Put its file in the data folder; "
                 "if it does not link by itself, choose the project on the Portfolio page.")
    _timeline(p)
