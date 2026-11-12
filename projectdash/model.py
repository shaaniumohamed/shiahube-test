"""Plain data objects shared by the reading logic and the screens.

Nothing in here knows about Excel or about the web UI, so either side can be
replaced later without touching the other.
"""
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any

# --- where a value came from (shown next to every value in the project page) ---
SRC_CORRECTION = "correction"
SRC_COLUMN = "column"
SRC_DETAIL = "detail file"
SRC_NOTES = "read from notes"
SRC_CALC = "calculated"
SRC_ASSUMED = "assumed from invoices"
SRC_INVOICE_SHEET = "INVOICE sheet"
SRC_NONE = "not found"

# --- delivery status of a project ---
D_NOT_STARTED = "Not started"
D_IN_PROGRESS = "In progress"
D_PARTLY = "Partly delivered"
D_DELIVERED = "Delivered"
D_UNKNOWN = "Unknown"
DELIVERY_STATUSES = [D_NOT_STARTED, D_IN_PROGRESS, D_PARTLY, D_DELIVERED]

# --- payment label of a project ---
P_UNPAID = "Unpaid"
P_PARTLY = "Partly paid"
P_NOT_SENT = "Invoice not sent"
P_NOT_INVOICED = "Not invoiced"
P_PAID = "Paid"
P_NOT_RECORDED = "Not recorded"
PAYMENT_LABELS = [P_UNPAID, P_PARTLY, P_NOT_SENT, P_NOT_INVOICED, P_PAID, P_NOT_RECORDED]

# --- overall status of a project, in the order the portfolio is sorted ---
S_LATE = "Late"
S_AT_RISK = "At risk"
S_UNCLEAR = "Unclear"
S_NO_DEADLINE = "No deadline"
S_ON_TRACK = "On track"
S_COMPLETE = "Complete"
S_PIPELINE = "Pipeline"
STATUS_ORDER = [S_LATE, S_AT_RISK, S_UNCLEAR, S_NO_DEADLINE, S_ON_TRACK, S_COMPLETE, S_PIPELINE]

# --- status of one line in a detail file ---
L_DELIVERED = "Delivered"
L_PARTIAL = "Partial"
L_PENDING = "Pending"
L_OUT_OF_STOCK = "Out of stock"
L_REORDERED = "Re-ordered"
L_CANCELLED = "Cancelled"
OPEN_LINE_STATUSES = (L_PARTIAL, L_PENDING, L_OUT_OF_STOCK)

# --- fields a Corrections row may set ---
CORRECTION_FIELDS = [
    "contract_value", "request_date", "agreement_date", "delivery_days", "due_date",
    "delivery_status", "payment_status", "unpaid", "next_action",
]


@dataclass
class Sourced:
    """A value together with where it came from."""
    value: Any = None
    source: str = SRC_NONE
    note: str = ""

    @property
    def found(self) -> bool:
        return self.value is not None and self.value != ""


@dataclass
class Flag:
    """One plain-English "Needs attention" item."""
    code: str
    text: str
    level: str = "attention"   # "urgent", "attention" or "info" (info is not counted)


@dataclass
class Invoice:
    number: str
    amount: float | None = None
    amount_source: str = SRC_NOTES
    sheet_status: str = ""          # payment status text from the INVOICE sheet, if any
    sheet_amount: float | None = None
    sheet_dispatched: dt.date | None = None


@dataclass
class TimelineEntry:
    date: dt.date
    text: str
    where: str = ""                 # which column it was read from
    is_new: bool = False            # appeared since the previous version of the file


@dataclass
class Line:
    """One line item of a project detail file."""
    excel_row: int
    num: str = ""
    article: str = ""
    description: str = ""
    unit: str = ""
    qty: float | None = None
    delivered: float | None = None
    vendor: str = ""
    vendor_quote: str = ""
    quotation: str = ""
    sap_quotation: str = ""
    sales_order: str = ""
    pr_po: str = ""
    client_po: str = ""
    delivery_note: str = ""
    delivery_note_kind: str = ""    # "DN" (manual DN-YYYY-nnn), "SAP" (7100…) or ""
    invoice: str = ""
    value: float | None = None
    dispatched: dt.date | None = None
    eta: dt.date | None = None
    site: str = ""
    remark: str = ""
    notes: str = ""                 # text from unnamed columns
    extra: dict[str, Any] = field(default_factory=dict)   # columns the app doesn't know
    # --- worked out by the app ---
    effective_qty: float | None = None
    status: str = L_PENDING
    conflict: bool = False          # remark says pending/out of stock, quantities say delivered
    reordered_as: str = ""          # "#" of the later line that re-orders this one
    reorder_of: str = ""            # "#" of the earlier line this one re-orders
    sheet: str = ""
    file: str = ""

    @property
    def balance(self) -> float | None:
        if self.qty is None:
            return None
        return self.qty - (self.delivered or 0)

    @property
    def active(self) -> bool:
        return self.status not in (L_REORDERED, L_CANCELLED)

    @property
    def open(self) -> bool:
        return self.status in OPEN_LINE_STATUSES


@dataclass
class Progress:
    active_lines: int = 0
    delivered_lines: int = 0
    by_lines: float | None = None      # 0–100
    by_qty: float | None = None
    by_value: float | None = None
    basis: str = ""                    # "value" or "line count"

    @property
    def percent(self) -> float | None:
        return self.by_value if self.basis == "value" else self.by_lines


@dataclass
class DetailFile:
    path: str
    name: str
    sheets: list[str] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)
    customer_codes: list[str] = field(default_factory=list)
    customer_name: str = ""
    sales_orders: list[str] = field(default_factory=list)
    unknown_columns: list[str] = field(default_factory=list)
    progress: Progress = field(default_factory=Progress)
    flags: list[Flag] = field(default_factory=list)
    conflict_lines: list[str] = field(default_factory=list)
    reorders: list[tuple[str, str]] = field(default_factory=list)
    gi_to_make: int = 0
    gi_to_reverse: int = 0
    reused_articles: list[str] = field(default_factory=list)
    linked_to: str | None = None       # project key
    link_reason: str = ""
    delivered_change: int | None = None  # delivered lines vs the previous version of the file


@dataclass
class Project:
    key: str
    row: int
    name: str
    client: str = ""
    register_file: str = ""
    raw: dict[str, Any] = field(default_factory=dict)       # original cells by header
    status_text: str = ""
    remarks_text: str = ""
    payment_text: str = ""
    values: dict[str, Sourced] = field(default_factory=dict)
    invoices: list[Invoice] = field(default_factory=list)
    received: float | None = None
    balance: float | None = None
    not_sent: float | None = None
    timeline: list[TimelineEntry] = field(default_factory=list)
    last_activity: dt.date | None = None
    detail_files: list[DetailFile] = field(default_factory=list)
    progress: Progress | None = None
    status: str = S_UNCLEAR
    status_reasons: list[str] = field(default_factory=list)
    days_to_due: int | None = None     # negative = days late
    flags: list[Flag] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)        # correction fields worth filling
    is_new: bool = False

    def get(self, name: str) -> Any:
        s = self.values.get(name)
        return s.value if s else None

    def source(self, name: str) -> str:
        s = self.values.get(name)
        return s.source if s else SRC_NONE

    @property
    def lines(self) -> list[Line]:
        return [ln for f in self.detail_files for ln in f.lines]

    @property
    def attention(self) -> list[Flag]:
        return [f for f in self.flags if f.level != "info"]

    @property
    def signed(self) -> bool:
        return self.status != S_PIPELINE

    @property
    def new_entries(self) -> list[TimelineEntry]:
        return [t for t in self.timeline if t.is_new]


@dataclass
class FileReport:
    """What the app made of one file in the data folder."""
    name: str
    kind: str                # "register", "detail file", "corrections", "skipped", "problem"
    detail: str = ""


@dataclass
class UnmatchedInvoice:
    number: str
    amount: float | None
    project_text: str
    customer: str
    status: str
    dispatched: dt.date | None = None


@dataclass
class NewNote:
    """A line of notes that was not in the previous version of the register."""
    project_key: str
    project_name: str
    text: str
    where: str
    date: dt.date | None = None


@dataclass
class Portfolio:
    as_of: dt.date
    folder: str
    projects: list[Project] = field(default_factory=list)
    unlinked: list[DetailFile] = field(default_factory=list)
    files: list[FileReport] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)       # plain-English reading problems
    unmatched_invoices: list[UnmatchedInvoice] = field(default_factory=list)
    new_notes: list[NewNote] = field(default_factory=list)
    previous_version: str = ""                              # when the previous register was seen
    is_sample: bool = False

    def project(self, key: str) -> Project | None:
        for p in self.projects:
            if p.key == key:
                return p
        return None

    @property
    def detail_files(self) -> list[DetailFile]:
        return [f for p in self.projects for f in p.detail_files] + list(self.unlinked)
