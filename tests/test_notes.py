import datetime as dt

import pytest

from projectdash import model as M
from projectdash import notes as N


@pytest.mark.parametrize("text, expected", [
    ("04.12.2023-Proposal submitted; 11.12.2023 -  Project awarded_x000B_15.01.2024 - Agreement Signed_x000B_PR Created",
     dt.date(2024, 1, 15)),
    ("Agreement Signed on- 25.11.2024\nAgreement Reference-60-LA/CON-L/2024/900", dt.date(2024, 11, 25)),
    ("PROJECT TIME LINE:\nSigned date:02.10.2024\nPO date: (4510001001) 07.10.2024", dt.date(2024, 10, 2)),
    ("Final draft shared on 11.06.2024\nContract signed 27th June 2024", dt.date(2024, 6, 27)),
    ("Agreement # (AGR)IRC/60/2024/05\nSinged on 27th June 2024", dt.date(2024, 6, 27)),
    ("Agreement Signed on 10th June 2024", dt.date(2024, 6, 10)),
])
def test_agreement_date_examples(text, expected):
    assert N.agreement_date(text)[0] == expected


def test_agreement_date_ignores_delivery_notes_and_undated_signing():
    assert N.agreement_date("items delivered on 26.08.2024- signed delivery note received") is None
    assert N.agreement_date("Agreement signed\nAgreement # 70-PA/CON-P/2024/415\n"
                            "Invoice dispatched on - 13.08.2024") is None
    assert N.agreement_date("Final draft agreement shared on 28.08.2024\nWaiting on finance for "
                            "the outstanding update\nAgreement signing process") is None
    assert N.agreement_date("New design approved on 01.02.2024") is None


def test_agreement_date_is_searched_in_status_then_remarks():
    assert N.agreement_date("Quotation submitted on 08th July 2024",
                            "Signed date:02.10.2024")[0] == dt.date(2024, 10, 2)


def test_delivery_period():
    assert N.delivery_days("75 days") == (75, M.SRC_COLUMN)
    assert N.delivery_days("45 Days") == (45, M.SRC_COLUMN)
    assert N.delivery_days(30) == (30, M.SRC_COLUMN)
    assert N.delivery_days(None, "x", "PO date: 07.10.2024\nDURATION- 35 Days") == (35, M.SRC_NOTES)
    assert N.delivery_days("Completed", "nothing here") is None


def test_invoices_numbers_amounts_and_duplicates():
    invoices = N.find_invoices(
        "Invoice (Pipes) - 6100006101 - Mvr 3,000,100.00 (Dispatched on 01.09.2024)",
        "6100006101 - Mvr 3,000,100.00\nINV-921000111\nInv-6100003311 - dispatched on 20.07.2024\n"
        "PO-4510000301 Sales order-3100003001 PO-1163240999")
    assert [(i.number, i.amount) for i in invoices] == [
        ("6100006101", 3000100.00), ("921000111", None), ("6100003311", None)]
    assert N.invoice_total(invoices) is None


def test_invoice_list_with_tabs():
    invoices = N.find_invoices("6100012001\t            300,000.05\n6100012002\t   19,000.00\n")
    assert N.invoice_total(invoices) == 319000.05


@pytest.mark.parametrize("text, label", [
    ("NOT CLEARED", M.P_UNPAID), ("partially cleared", M.P_PARTLY),
    ("partially cleared\n(Signed delivery note pending)", M.P_PARTLY),
    ("need to dispatched", M.P_NOT_SENT), ("not invoice\n(Site C - 2025-031)", M.P_NOT_INVOICED),
    ("COMPLETED", M.P_PAID), ("Cleared", M.P_PAID), ("", None), ("see finance", None),
])
def test_payment_labels(text, label):
    assert N.payment_label_from_text(text) == label


def test_payment_label_falls_back_to_remarks_then_to_not_recorded():
    assert N.payment_label(None, "Completed.\nInvoice dispatched", True) == (M.P_PAID, M.SRC_NOTES)
    assert N.payment_label(None, "6100005001 (900,000.00)", True)[0] == M.P_NOT_RECORDED
    assert N.payment_label(None, "ONGOING", False)[0] is None


def test_received_and_balance():
    assert N.received_amount("Payment received - 7,000,000.00") == 7000000.00
    assert N.received_amount("payment received - 200,000.00 on 31st Dec 2024") == 200000.00
    assert N.received_amount("Received Advance payment on 10.10.2024 (2,000,000.25) ") == 2000000.25
    assert N.balance_amount("Payment received - 7,000,000.00\nBalance  - 1,450,120.40") == 1450120.40
    assert N.balance_amount("Balace - 160000.") is None


def _inv(*amounts):
    return [M.Invoice(f"61000000{i:02d}", a) for i, a in enumerate(amounts)]


def test_unpaid_rules():
    assert N.unpaid_amount(M.P_PAID, _inv(100.0), None, None)[0] == 0
    assert N.unpaid_amount(M.P_NOT_INVOICED, [], None, None)[0] == 0
    assert N.unpaid_amount(M.P_NOT_SENT, _inv(500.0), None, None)[0] == 0
    assert N.not_sent_amount(M.P_NOT_SENT, _inv(500.0)) == 500.0
    assert N.unpaid_amount(M.P_UNPAID, _inv(100.0, 250.5), None, None)[0] == 350.5
    assert N.unpaid_amount(M.P_UNPAID, _inv(100.0, None), None, None)[0] is None
    assert N.unpaid_amount(M.P_PARTLY, _inv(100.0), 40.0, 55.0)[0] == 55.0      # balance wins
    assert N.unpaid_amount(M.P_PARTLY, _inv(100.0), 40.0, None)[0] == 60.0
    assert N.unpaid_amount(M.P_PARTLY, _inv(100.0), 400.0, None)[0] is None     # over-received
    assert N.unpaid_amount(M.P_PARTLY, _inv(100.0), None, None)[0] is None
    assert N.unpaid_amount(M.P_NOT_RECORDED, _inv(100.0), None, None)[0] is None


@pytest.mark.parametrize("text, expected", [
    ("Plan to propose suitable models to identify their need", M.D_NOT_STARTED),
    ("Held a meeting with the procurement team", M.D_NOT_STARTED),
    ("Final draft shared on 28.08.2024\nAgreement signing process", M.D_NOT_STARTED),
    ("Proposal submitted for 2 units\nCOMPLETED-", M.D_DELIVERED),
    ("ONGOING\nsales order need to be amended", M.D_IN_PROGRESS),
    ("1st Lot\n5- vans Handovered\n3rd Lot\nETA-9th May", M.D_PARTLY),
    ("item delivered, Shortage 40 EA Bolt", M.D_PARTLY),
    ("Unit delivered on 05.11.2024 | partially cleared", M.D_DELIVERED),
    ("DELIVERED- INVOICE PENDING", M.D_DELIVERED),
    ("Draft agreement shared with legal\n6100016001 (MVR 400,100.24)", M.D_UNKNOWN),
])
def test_delivery_status_from_text(text, expected):
    assert N.delivery_status_from_text(text) == expected


def test_timeline_newest_first_and_date_only_lines_join_the_next_line():
    entries = N.timeline({"Status": "04.12.2023-Proposal submitted; 11.12.2023 - Awarded\n"
                                    "15.01.2024\nAgreement signed\nPR created"})
    assert [(e.date, e.text) for e in entries] == [
        (dt.date(2024, 1, 15), "15.01.2024 Agreement signed"),
        (dt.date(2023, 12, 11), "11.12.2023 - Awarded"),
        (dt.date(2023, 12, 4), "04.12.2023-Proposal submitted")]


def test_last_activity_ignores_future_plans_and_typo_detection():
    entries = N.timeline({"Remarks": "Invoice sent 05.02.2025\nSchedule to clear on 28.11.2026"})
    assert N.last_activity(entries, dt.date(2025, 11, 10)) == dt.date(2025, 2, 5)
    odd = N.timeline({"Status": "28.12.2023-Proposal\n15.01.2023 - guarantee submitted"})
    assert N.suspicious_dates(odd, dt.date(2023, 12, 20)) == [dt.date(2023, 1, 15)]
    assert N.suspicious_dates(odd, None) == []
