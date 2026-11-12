"""Payments: invoiced, unpaid and not-yet-sent amounts (secondary to delivery)."""
from __future__ import annotations

import streamlit as st

import ui
from projectdash import model as M
from projectdash.notes import invoice_total

PAY_COLOR = {M.P_UNPAID: "#d03b3b", M.P_PARTLY: "#fab219", M.P_NOT_SENT: "#ec835a",
             M.P_NOT_INVOICED: "#c3c2b7", M.P_PAID: "#0ca30c", M.P_NOT_RECORDED: "#898781"}
ORDER = [M.P_UNPAID, M.P_PARTLY, M.P_NOT_SENT, M.P_NOT_RECORDED, M.P_NOT_INVOICED, M.P_PAID]


def render() -> None:
    c = ui.ctx()
    pf, cfg = c["pf"], c["cfg"]
    currency = cfg.get("currency", "")
    ui.head("Payments", "Read from the notes and the payment column of the master list. "
                        "Amounts the notes don't state are shown as unclear, never guessed.")
    signed = [p for p in pf.projects if p.signed]
    if not signed:
        ui.empty("No signed projects yet.")
        return
    owed = [p for p in signed if p.get("payment_status") in (M.P_UNPAID, M.P_PARTLY)]
    unpaid = sum(p.get("unpaid") or 0 for p in owed)
    unclear = [p for p in owed if p.get("unpaid") is None]
    invoiced = sum(invoice_total(p.invoices) or 0 for p in signed)
    partial_inv = sum(1 for p in signed if p.invoices and invoice_total(p.invoices) is None)
    not_sent = sum(p.not_sent or 0 for p in signed)
    contract = sum(p.get("contract_value") or 0 for p in signed)
    ui.tiles([
        {"label": "Contract value (signed)", "value": ui.money(contract, compact=True),
         "unit": currency, "title": ui.money(contract), "sub": f"{len(signed)} projects"},
        {"label": "Invoiced (known)", "value": ui.money(invoiced, compact=True), "unit": currency,
         "title": ui.money(invoiced),
         "sub": f"{partial_inv} project{'s' if partial_inv != 1 else ''} with an amount missing"
         if partial_inv else "from invoice amounts in the notes"},
        {"label": "Unpaid (known)", "value": ui.money(unpaid, compact=True), "unit": currency,
         "title": ui.money(unpaid), "tone": "alert" if unpaid else "",
         "sub": f"{len(unclear)} more unclear" if unclear else f"across {len(owed)} projects"},
        {"label": "Invoiced, not yet sent", "value": ui.money(not_sent, compact=True),
         "unit": currency, "title": ui.money(not_sent), "tone": "warn" if not_sent else "",
         "sub": "invoice exists but has not gone to the client"},
    ])

    ui.h2("By project")
    choice = st.pills("Payment status", [s for s in ORDER if any(
        (p.get("payment_status") or "") == s for p in signed)], selection_mode="multi",
        key="pay_filter", label_visibility="collapsed")
    rows = []
    listed = sorted(signed, key=lambda p: (ORDER.index(p.get("payment_status"))
                                           if p.get("payment_status") in ORDER else 99,
                                           -(p.get("unpaid") or 0)))
    for p in listed:
        pay = p.get("payment_status")
        if choice and pay not in choice:
            continue
        if not pay and not p.invoices:
            continue
        total = invoice_total(p.invoices)
        unpaid_value = p.get("unpaid")
        unpaid_text = (ui.money(unpaid_value) if unpaid_value is not None else
                       "<b>Unclear</b>" if pay in (M.P_UNPAID, M.P_PARTLY, M.P_NOT_RECORDED) else "—")
        rows.append([
            f'<div class="wide"><a class="lnk" href="{ui.esc(ui.project_href(p))}" target="_self">'
            f'{ui.esc(p.name[:90])}</a><div class="sub">{ui.esc(p.client)}</div></div>',
            ui.chip(pay, PAY_COLOR) if pay else '<span class="muted">—</span>',
            ui.money(p.get("contract_value")),
            ui.money(total) if total is not None else
            (f'<span class="muted">{len(p.invoices)} invoice(s), amount missing</span>' if p.invoices else "—"),
            ui.money(p.received) if p.received is not None else "—",
            unpaid_text,
            "<br>".join(ui.esc(i.number) for i in p.invoices) or '<span class="muted">none recorded</span>'])
    if rows:
        ui.table(["Project", "Payment", "Contract value", "Invoiced", "Received", "Unpaid", "Invoices"],
                 rows, right={2, 3, 4, 5})
    else:
        ui.empty("No project matches.")

    notes = [(p, f) for p in signed for f in p.flags
             if f.code in ("invoice_sheet_disagrees", "invoice_amount_differs")]
    if notes or pf.unmatched_invoices:
        ui.h2("Cross-check with the INVOICE sheet",
              "the master list stays the main source; these are differences to look at")
    if notes:
        ui.table(["Project", "Difference"], [[
            f'<a class="lnk" href="{ui.esc(ui.project_href(p))}" target="_self">{ui.esc(p.name[:70])}</a>',
            ui.esc(f.text)] for p, f in notes])
    if pf.unmatched_invoices:
        st.caption(f"{len(pf.unmatched_invoices)} invoice(s) in the INVOICE sheet are not mentioned "
                   "in any project's notes:")
        ui.table(["Invoice", "Amount", "Described as", "Customer", "Dispatched", "Payment status"], [[
            f'<span class="num">{ui.esc(u.number)}</span>', ui.money(u.amount), ui.esc(u.project_text),
            ui.esc(u.customer), ui.day(u.dispatched), ui.esc(u.status)]
            for u in pf.unmatched_invoices], right={1})
