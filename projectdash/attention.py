""""Needs attention" items: plain-English findings worked out from the data."""
from __future__ import annotations

import datetime as dt

from . import model as M
from . import notes
from .textnorm import as_text


def money(value: float | None) -> str:
    return "—" if value is None else f"{value:,.2f}"


def day(value: dt.date | None) -> str:
    return "—" if value is None else value.strftime("%d.%m.%Y")


def _plural(n: int, word: str = "day") -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def project_flags(p: M.Project, as_of: dt.date, cfg: dict) -> tuple[list[M.Flag], list[str]]:
    """Returns (flags, correction fields worth filling in)."""
    flags: list[M.Flag] = []
    missing: list[str] = []
    delivery = p.get("delivery_status")
    pay = p.get("payment_status")
    due = p.get("due_date")
    contract = p.get("contract_value")
    total = notes.invoice_total(p.invoices)
    open_project = p.status not in (M.S_COMPLETE, M.S_PIPELINE)

    # ---- delivery and deadlines
    if p.status == M.S_LATE and p.days_to_due is not None:
        flags.append(M.Flag("late", f"Delivery is {_plural(-p.days_to_due)} past the due date "
                                    f"({day(due)}).", "urgent"))
    if p.status == M.S_AT_RISK:
        flags.append(M.Flag("at_risk", "At risk: " + " ".join(p.status_reasons), "urgent"))
    if delivery == M.D_UNKNOWN:
        flags.append(M.Flag("delivery_unknown", "Delivery status isn't stated in the notes."))
        missing.append("delivery_status")
    if p.source("delivery_status") == M.SRC_ASSUMED:
        flags.append(M.Flag(
            "assumed_delivered",
            "Treated as delivered because the full contract value is invoiced; "
            "the notes never say so.", "info"))
    if open_project:
        if not p.get("agreement_date") and not due:
            flags.append(M.Flag("no_agreement_date", "No agreement signing date found."))
            missing.append("agreement_date")
        if not p.get("delivery_days") and not due:
            flags.append(M.Flag("no_delivery_period",
                                "No delivery period recorded, so lateness can't be tracked."))
            missing.append("delivery_days")

    # ---- money
    if pay == M.P_NOT_RECORDED:
        flags.append(M.Flag("payment_not_recorded",
                            "An invoice was found but payment status isn't recorded."))
        missing.append("payment_status")
    if pay in (M.P_UNPAID, M.P_PARTLY) and p.get("unpaid") is None:
        why = p.values["unpaid"].note
        flags.append(M.Flag(
            "unpaid_unclear",
            f"Marked {pay.lower()} but the outstanding amount isn't clear"
            + (f" ({why})." if why else ".")))
        missing.append("unpaid")
    if pay == M.P_UNPAID and not p.invoices:
        flags.append(M.Flag("unpaid_no_invoice",
                            "Marked not cleared but no invoice number is recorded."))
    if pay == M.P_NOT_SENT:
        amount = f"{money(p.not_sent)} was" if p.not_sent is not None else "An amount was"
        flags.append(M.Flag("invoice_not_sent",
                            f"{amount} invoiced but not yet sent to the client."))
    if (delivery == M.D_DELIVERED and p.source("delivery_status") != M.SRC_ASSUMED
            and total is not None and contract and total < contract - 1):
        flags.append(M.Flag(
            "under_invoiced",
            f"Delivered, but the invoices total {money(total)}, which is "
            f"{money(contract - total)} less than the contract value."))
    if p.signed and not contract and delivery != M.D_UNKNOWN:
        missing.append("contract_value")

    # ---- cross-check with the INVOICE sheet
    for inv in p.invoices:
        status = inv.sheet_status.lower()
        if pay == M.P_UNPAID and ("cleared" in status or status == "paid") \
                and "not" not in status:
            flags.append(M.Flag(
                "invoice_sheet_disagrees",
                f"The INVOICE sheet shows invoice {inv.number} as cleared, but the master "
                "list says not cleared."))
        if (inv.sheet_amount is not None and inv.amount is not None
                and inv.amount_source != M.SRC_INVOICE_SHEET
                and abs(inv.sheet_amount - inv.amount) > 0.01):
            flags.append(M.Flag(
                "invoice_amount_differs",
                f"Invoice {inv.number}: the notes say {money(inv.amount)} but the INVOICE "
                f"sheet says {money(inv.sheet_amount)}."))

    # ---- activity
    stale_days = int(cfg.get("stale_update_days", 30))
    finished = p.status == M.S_COMPLETE and pay == M.P_PAID
    if p.last_activity and not finished:
        idle = (as_of - p.last_activity).days
        if idle > stale_days:
            flags.append(M.Flag("stale", f"Last dated activity in the notes was "
                                         f"{_plural(idle)} ago ({day(p.last_activity)})."))
    for odd in notes.suspicious_dates(p.timeline, p.get("request_date"),
                                      int(cfg.get("date_typo_days", 30))):
        flags.append(M.Flag(
            "date_typo",
            f"Possible date typo: {day(odd)} in the notes is more than "
            f"{cfg.get('date_typo_days', 30)} days before the request date "
            f"({day(p.get('request_date'))})."))

    # ---- from the detail files
    for detail in p.detail_files:
        prefix = f"{detail.name}: " if len(p.detail_files) > 1 else ""
        for flag in detail.flags:
            flags.append(M.Flag(flag.code, prefix + flag.text, flag.level))
    if due:
        late = [ln for ln in p.lines if ln.open and ln.eta and ln.eta > due]
        if late:
            flags.append(M.Flag(
                "eta_after_due",
                f"{_plural(len(late), 'open line')} "
                f"{'has' if len(late) == 1 else 'have'} an ETA after the due date."))
    register_sos = {s for s in as_text(p.get("so_number")).replace("/", " ").split()}
    for detail in p.detail_files:
        other = [s for s in detail.sales_orders if s not in register_sos]
        if other and register_sos:
            flags.append(M.Flag(
                "other_sales_orders",
                f"The detail file uses Sales Order {', '.join(other)}; the master list shows "
                f"{', '.join(sorted(register_sos))}. Normal when a project has several.",
                "info"))

    order = {"urgent": 0, "attention": 1, "info": 2}
    flags.sort(key=lambda f: order.get(f.level, 1))
    return flags, missing
