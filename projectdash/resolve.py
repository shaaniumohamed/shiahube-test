"""Builds a project from a register row by applying the layers in priority order:

1. a row in the Corrections sheet
2. an optional new column in the master list (Agreement date, Due date, …)
3. the linked detail file (for delivery progress)
4. values read from the notes, or calculated

Every value keeps a label saying which layer it came from.
"""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

from . import model as M
from . import notes
from .lines import progress as line_progress
from .status import project_status
from .textnorm import as_text, to_date, to_int, to_number

_FIELD_ALIASES = {
    "value": "contract_value", "project_value": "contract_value", "contract": "contract_value",
    "request": "request_date",
    "agreement": "agreement_date", "signed_date": "agreement_date", "agreement_signed": "agreement_date",
    "delivery_period": "delivery_days", "days": "delivery_days", "period": "delivery_days",
    "deadline": "due_date", "due": "due_date",
    "delivery": "delivery_status", "status": "delivery_status",
    "payment": "payment_status",
    "outstanding": "unpaid", "balance": "unpaid",
    "action": "next_action", "next": "next_action",
}

FIELD_HELP = {
    "contract_value": "contract value as a number, e.g. 1250000.50",
    "request_date": "date the request came in, e.g. 18.12.2023",
    "agreement_date": "date the agreement was signed, e.g. 25.11.2024",
    "delivery_days": "agreed delivery period in days, e.g. 45",
    "due_date": "delivery due date, e.g. 31.01.2025 (only if it is not signing date + days)",
    "delivery_status": "Not started, In progress, Partly delivered or Delivered",
    "payment_status": "Unpaid, Partly paid, Invoice not sent, Not invoiced or Paid",
    "unpaid": "amount still owed by the client, e.g. 319529.17",
    "next_action": "what happens next, in a few words",
}


def correction_field(name: str) -> str | None:
    key = re.sub(r"[^a-z0-9]+", "_", as_text(name).strip().lower()).strip("_")
    key = _FIELD_ALIASES.get(key, key)
    return key if key in M.CORRECTION_FIELDS else None


def correction_value(field: str, raw: Any) -> Any:
    """Turn the typed value into the right kind of value, or raise ValueError."""
    if field in ("contract_value", "unpaid"):
        value = to_number(raw)
        if value is None:
            raise ValueError("needs a number")
        return value
    if field in ("request_date", "agreement_date", "due_date"):
        value = to_date(raw)
        if value is None:
            raise ValueError("needs a date such as 25.11.2024")
        return value
    if field == "delivery_days":
        value = to_int(raw)
        if value is None or value <= 0:
            raise ValueError("needs a number of days")
        return value
    if field == "delivery_status":
        value = notes.normalise_delivery_status(raw)
        if value is None:
            raise ValueError("needs one of: " + ", ".join(M.DELIVERY_STATUSES))
        return value
    if field == "payment_status":
        value = notes.normalise_payment_status(raw)
        if value is None:
            raise ValueError("needs one of: " + ", ".join(M.PAYMENT_LABELS[:5]))
        return value
    return " ".join(as_text(raw).split())


def base_project(row, table, key: str) -> M.Project:
    """The project as typed in the register, before any layer is applied."""
    c = row.cells
    return M.Project(
        key=key, row=row.row,
        name=" ".join(as_text(c.get("name")).split()),
        client=" ".join(as_text(c.get("client")).split()),
        register_file=table.file, raw=dict(row.raw),
        status_text=as_text(c.get("status")), remarks_text=as_text(c.get("remarks")),
        payment_text=as_text(row.payment_cell))


def register_sales_orders(row) -> set[str]:
    c = row.cells
    found = set(notes.sales_orders_in_text(c.get("so_number"), c.get("status"), c.get("remarks")))
    for number in re.findall(r"(?<!\d)\d{8,10}(?!\d)", as_text(c.get("so_number"))):
        found.add(number)
    return found


def _first(*options: M.Sourced) -> M.Sourced:
    for option in options:
        if option.found:
            return option
    return M.Sourced()


def detail_delivery_status(progress: M.Progress | None, lines: list[M.Line]) -> str | None:
    if not progress or not progress.active_lines:
        return None
    if progress.delivered_lines >= progress.active_lines:
        return M.D_DELIVERED
    if progress.delivered_lines > 0 or any(ln.status == M.L_PARTIAL for ln in lines):
        return M.D_PARTLY
    return M.D_IN_PROGRESS


def resolve_project(project: M.Project, row, corrections: dict[str, tuple[Any, str]],
                    invoice_rows: dict[str, Any], as_of: dt.date, cfg: dict) -> M.Project:
    """Fill in every value of the project with its source, then status."""
    c = row.cells
    status_cell, remarks_cell, payment_cell = c.get("status"), c.get("remarks"), row.payment_cell

    def corrected(field: str) -> M.Sourced:
        if field in corrections:
            value, note = corrections[field]
            return M.Sourced(value, M.SRC_CORRECTION, note)
        return M.Sourced()

    def column(value: Any, note: str = "") -> M.Sourced:
        return M.Sourced(value, M.SRC_COLUMN, note) if value not in (None, "") else M.Sourced()

    v: dict[str, M.Sourced] = {}
    v["contract_value"] = _first(corrected("contract_value"), column(to_number(c.get("value"))))
    v["request_date"] = _first(corrected("request_date"), column(to_date(c.get("request_date"))))

    read = notes.agreement_date(status_cell, remarks_cell)
    v["agreement_date"] = _first(
        corrected("agreement_date"),
        column(to_date(c.get("agreement_date"))),
        M.Sourced(read[0], M.SRC_NOTES, f'from "{read[1]}"') if read else M.Sourced())

    days = notes.delivery_days(c.get("delivery_period"), status_cell, remarks_cell)
    v["delivery_days"] = _first(
        corrected("delivery_days"),
        M.Sourced(days[0], days[1],
                  "from the notes" if days[1] == M.SRC_NOTES else "") if days else M.Sourced())

    agreement, period = v["agreement_date"].value, v["delivery_days"].value
    calculated = M.Sourced()
    if agreement and period:
        calculated = M.Sourced(agreement + dt.timedelta(days=int(period)), M.SRC_CALC,
                               f"agreement date + {period} days")
    v["due_date"] = _first(corrected("due_date"), column(to_date(c.get("due_date"))), calculated)

    # ---- invoices and money
    invoices = notes.find_invoices(status_cell, remarks_cell, payment_cell)
    for inv in invoices:
        sheet_row = invoice_rows.get(inv.number)
        if sheet_row is None:
            continue
        inv.sheet_status, inv.sheet_amount = sheet_row.status, sheet_row.amount
        inv.sheet_dispatched = sheet_row.dispatched
        if inv.amount is None and sheet_row.amount is not None:
            inv.amount, inv.amount_source = sheet_row.amount, M.SRC_INVOICE_SHEET
    project.invoices = invoices
    project.received = notes.received_amount(status_cell, remarks_cell)
    project.balance = notes.balance_amount(status_cell, remarks_cell)

    label, label_source = notes.payment_label(payment_cell, remarks_cell, bool(invoices))
    v["payment_status"] = _first(
        corrected("payment_status"),
        M.Sourced(label, label_source,
                  "an invoice exists but no payment status is typed"
                  if label == M.P_NOT_RECORDED else "") if label else M.Sourced())
    pay = v["payment_status"].value
    amount, amount_source, why = notes.unpaid_amount(pay, invoices, project.received, project.balance)
    v["unpaid"] = _first(corrected("unpaid"),
                         M.Sourced(amount, amount_source, why) if amount is not None
                         else M.Sourced(None, M.SRC_NONE, why))
    if not v["unpaid"].found and v["unpaid"].value != 0:
        v["unpaid"] = M.Sourced(None, M.SRC_NONE, why)
    project.not_sent = notes.not_sent_amount(pay, invoices)
    total = notes.invoice_total(invoices)
    v["invoiced"] = (M.Sourced(total, M.SRC_CALC, f"sum of {len(invoices)} invoice(s)")
                     if total is not None else
                     M.Sourced(None, M.SRC_NONE, "an invoice amount is missing" if invoices else ""))

    # ---- delivery
    project.progress = line_progress(project.lines) if project.detail_files else None
    from_detail = detail_delivery_status(project.progress, project.lines)
    from_text = notes.delivery_status_from_text(status_cell, remarks_cell)
    assumed = M.Sourced()
    contract = v["contract_value"].value
    if (from_text == M.D_UNKNOWN and cfg.get("assume_delivered_when_fully_invoiced", True)
            and total is not None and contract
            and total >= contract * float(cfg.get("fully_invoiced_percent", 99.5)) / 100):
        assumed = M.Sourced(M.D_DELIVERED, M.SRC_ASSUMED,
                            "the notes don't say delivered, but the full value is invoiced")
    v["delivery_status"] = _first(
        corrected("delivery_status"),
        column(notes.normalise_delivery_status(c.get("delivery_status"))),
        M.Sourced(from_detail, M.SRC_DETAIL,
                  f"{project.progress.delivered_lines} of {project.progress.active_lines} "
                  "lines delivered") if from_detail else M.Sourced(),
        M.Sourced(from_text, M.SRC_NOTES) if from_text != M.D_UNKNOWN else M.Sourced(),
        assumed)
    if not v["delivery_status"].found:
        v["delivery_status"] = M.Sourced(M.D_UNKNOWN, M.SRC_NONE)

    v["next_action"] = _first(corrected("next_action"),
                              column(" ".join(as_text(c.get("next_action")).split())))
    for name in ("order_type", "pr_number", "pr_date", "so_number", "project_id"):
        v[name] = column(" / ".join(as_text(c.get(name)).split()))
    project.values = v

    # ---- activity
    cells = {"Status": status_cell, "Remarks": remarks_cell, "Payment": payment_cell}
    project.timeline = notes.timeline(cells)
    project.last_activity = notes.last_activity(project.timeline, as_of)

    # ---- overall status
    percent = project.progress.percent if project.progress else None
    etas = [ln.eta for ln in project.lines if ln.open and ln.eta]
    project.status, project.status_reasons, project.days_to_due = project_status(
        v["delivery_status"].value, v["agreement_date"].value, v["due_date"].value,
        as_of, percent, etas, cfg)
    return project
