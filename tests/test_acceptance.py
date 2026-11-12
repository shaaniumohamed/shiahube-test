"""End-to-end checks on the made-up sample files, as of 10 Nov 2025.

Each test mirrors one acceptance check of the real files, with invented
projects that have the same quirks.
"""
import datetime as dt

import openpyxl
import pytest

from projectdash import load_portfolio
from projectdash import model as M
from projectdash.export import corrections_workbook, table_rows
from projectdash.state import StateStore
from tools import sample_data

from .conftest import AS_OF, codes, find


# ------------------------------------------------------------------ register
def test_master_sheet_is_chosen_and_summary_rows_are_skipped(pf):
    assert len(pf.projects) == len(sample_data.PROJECTS) == 23
    report = next(f for f in pf.files if f.kind == "register")
    assert "sheet 'Sheet1'" in report.detail and "headers in row 5" in report.detail
    assert "Sheet2" in report.detail                     # listed as not used
    assert not pf.problems


def test_hidden_rows_are_still_read(pf):
    assert find(pf, "City Library").status == M.S_PIPELINE


def test_float_artifacts_are_rounded(pf):
    assert find(pf, "12 Units").get("contract_value") == 8450120.40
    assert find(pf, "South Atoll Dewatering - Additional").get("contract_value") == 420000.60


def test_vans_partly_delivered_partly_paid_and_late(pf):
    p = find(pf, "12 Units")
    assert p.name == "Procurement ( 12 Units) vans"
    assert p.get("request_date") == dt.date(2023, 12, 4)
    assert (p.get("agreement_date"), p.source("agreement_date")) == (dt.date(2024, 1, 15), M.SRC_NOTES)
    assert (p.get("delivery_days"), p.source("delivery_days")) == (75, M.SRC_COLUMN)
    assert (p.get("due_date"), p.source("due_date")) == (dt.date(2024, 3, 30), M.SRC_CALC)
    assert p.get("delivery_status") == M.D_PARTLY
    assert (p.get("payment_status"), p.source("payment_status")) == (M.P_PARTLY, M.SRC_COLUMN)
    assert p.received == 7000000.00
    assert (p.get("unpaid"), p.source("unpaid")) == (1450120.40, M.SRC_NOTES)
    assert p.status == M.S_LATE and p.days_to_due == -590
    assert "late" in codes(p)


def test_invoice_amount_filled_from_invoice_sheet_as_cross_check(pf):
    inv = find(pf, "12 Units").invoices[0]
    assert (inv.number, inv.amount, inv.amount_source) == ("6100003311", 8450220.40, M.SRC_INVOICE_SHEET)


def test_duration_in_notes_and_advance_payment(pf):
    p = find(pf, "PHASE-II")
    assert p.get("agreement_date") == dt.date(2024, 10, 2)
    assert (p.get("delivery_days"), p.source("delivery_days")) == (35, M.SRC_NOTES)
    assert p.get("due_date") == dt.date(2024, 11, 6)
    assert [(i.number, i.amount) for i in p.invoices] == [("6100015001", 1100000.50)]
    assert p.received == 2000000.25
    assert p.get("unpaid") is None                       # more received than invoiced: unclear
    assert "unpaid_unclear" in codes(p)
    assert p.get("delivery_status") == M.D_DELIVERED     # known limitation, see correction test


def test_balance_in_notes(pf):
    p = find(pf, "East Lagoon Road")
    assert p.get("agreement_date") == dt.date(2024, 6, 10)
    assert p.balance == 300000.00 and p.get("unpaid") == 300000.00
    assert p.last_activity == dt.date(2024, 12, 31)


def test_misspelt_balance_is_not_used(pf):
    p = find(pf, "CREW IDENTITY CARD")
    assert p.balance is None and p.get("unpaid") is None
    assert p.get("delivery_status") == M.D_UNKNOWN and p.status == M.S_UNCLEAR
    assert {"delivery_unknown", "unpaid_unclear", "no_agreement_date"} <= codes(p)


def test_possible_date_typo(pf):
    typo = [f for f in find(pf, "Studio mixer").flags if f.code == "date_typo"]
    assert len(typo) == 1 and "15.01.2023" in typo[0].text


def test_pipeline_projects(pf):
    assert {p.name for p in pf.projects if p.status == M.S_PIPELINE} == {
        "Procurement of Patrol boat", "Replacement of Archive hall roofing",
        "City Library Renovation"}


def test_invoice_not_sent(pf):
    p = find(pf, "Long Island")
    assert p.get("payment_status") == M.P_NOT_SENT
    assert p.not_sent == 2500000.04 and p.get("unpaid") == 0
    assert "invoice_not_sent" in codes(p)


def test_fully_invoiced_is_assumed_delivered(pf):
    p = find(pf, "Long Island")
    assert (p.get("delivery_status"), p.source("delivery_status")) == (M.D_DELIVERED, M.SRC_ASSUMED)
    assert p.status == M.S_COMPLETE
    assert "assumed_delivered" in codes(p) and "assumed_delivered" not in {f.code for f in p.attention}


def test_assumption_can_be_switched_off(cfg, sample_dir):
    off = dict(cfg, assume_delivered_when_fully_invoiced=False)
    p = find(load_portfolio(off, AS_OF, folder=str(sample_dir)), "Long Island")
    assert p.get("delivery_status") == M.D_UNKNOWN and p.status == M.S_LATE


def test_shortage_means_partly_delivered(pf):
    p = find(pf, "Dewatering - Additional")
    assert p.get("delivery_status") == M.D_PARTLY and p.status == M.S_NO_DEADLINE


def test_six_invoices_separated_by_tabs(pf):
    p = find(pf, "cell block")
    assert len(p.invoices) == 6
    assert p.get("invoiced") == 2189001.96 == p.get("unpaid")


def test_invoice_repeated_in_status_and_remarks_counts_once(pf):
    p = [x for x in pf.projects if x.name.endswith("South Atoll Dewatering")][0]
    assert p.get("agreement_date") == dt.date(2024, 6, 27)          # "Singed on"
    assert [i.number for i in p.invoices] == ["6100006101", "6100006102"]
    assert p.get("unpaid") == 4200300.60


def test_payment_flags(pf):
    assert "payment_not_recorded" in codes(find(pf, "Survey Equipments"))
    assert "unpaid_no_invoice" in codes(find(pf, "EQUIPMENT SUPPLY- PHASE-I"))
    assert "under_invoiced" in codes(find(pf, "UPVC Pipes for West Island"))
    assert find(pf, "Sports flooring").get("payment_status") == M.P_NOT_INVOICED
    assert find(pf, "Studio mixer").get("payment_status") == M.P_PAID


def test_invoice_sheet_cross_check(pf):
    assert "invoice_sheet_disagrees" in codes(find(pf, "20004567"))
    assert "invoice_amount_differs" in codes(find(pf, "Dewatering - Additional"))
    assert [u.number for u in pf.unmatched_invoices] == ["6100014999"]


def test_invoice_sheet_can_be_switched_off(cfg, sample_dir):
    off = load_portfolio(dict(cfg, use_invoice_sheet=False), AS_OF, folder=str(sample_dir))
    assert find(off, "12 Units").invoices[0].amount is None
    assert "invoice_sheet_disagrees" not in codes(find(off, "20004567"))


# ------------------------------------------------------------------ status logic
def test_status_examples(pf):
    at_risk = find(pf, "Solar street lights")
    assert at_risk.get("due_date") == dt.date(2025, 11, 19)
    assert at_risk.status == M.S_AT_RISK and at_risk.days_to_due == 9
    on_track = find(pf, "LED floodlights")
    assert on_track.status == M.S_ON_TRACK and on_track.get("delivery_status") == M.D_IN_PROGRESS
    assert find(pf, "Sports flooring").status == M.S_NO_DEADLINE
    assert find(pf, "Health Awareness").status == M.S_COMPLETE


def test_as_of_date_changes_the_status(cfg, sample_dir):
    early = load_portfolio(cfg, dt.date(2025, 10, 25), folder=str(sample_dir))
    assert find(early, "Solar street lights").status == M.S_ON_TRACK
    later = load_portfolio(cfg, dt.date(2025, 12, 1), folder=str(sample_dir))
    assert find(later, "Solar street lights").status == M.S_LATE


def test_portfolio_is_sorted_worst_first(pf):
    order = [M.STATUS_ORDER.index(p.status) for p in pf.projects]
    assert order == sorted(order)
    assert pf.projects[0].status == M.S_LATE


def test_stale_flag_skips_projects_that_are_complete_and_paid(pf):
    assert "stale" in codes(find(pf, "12 Units"))
    assert "stale" not in codes(find(pf, "Studio mixer"))
    assert "stale" not in codes(find(pf, "LED floodlights"))       # updated 5 days ago


# ------------------------------------------------------------------ detail file
@pytest.fixture(scope="module")
def works(pf):
    return find(pf, "20004567")


def test_detail_file_links_by_customer_code(works, pf):
    assert [d.name for d in works.detail_files] == [sample_data.DETAIL_NAME]
    assert works.detail_files[0].link_reason == "customer code 20004567"
    assert [d.name for d in pf.unlinked] == [sample_data.SECOND_DETAIL_NAME]


def test_detail_project_dates_and_money(works):
    assert works.get("agreement_date") == dt.date(2024, 11, 25)
    assert works.get("due_date") == dt.date(2024, 12, 25)
    assert [(i.number, i.amount) for i in works.invoices] == [
        ("6100019001", 800000.38), ("6100020001", 200000.80)]
    assert works.get("unpaid") == 1000001.18
    assert works.status == M.S_LATE


def test_reorders_and_active_lines(works):
    d = works.detail_files[0]
    assert len(d.lines) == 38
    assert [ln.num for ln in d.lines][16:26] == ["17", "18", "19", "21", "22", "24", "23", "25", "20", "26"]
    assert set(d.reorders) == {("18", "34"), ("19", "33"), ("20", "35"), ("26", "36")}
    assert (d.progress.active_lines, d.progress.delivered_lines) == (35, 25)
    assert d.progress.basis == "line count" and d.progress.by_lines == 71.4
    by_num = {ln.num: ln for ln in d.lines}
    assert by_num["18"].status == M.L_REORDERED and not by_num["18"].active
    assert by_num["19"].status == M.L_DELIVERED and by_num["19"].effective_qty == 3
    assert by_num["30"].status == M.L_OUT_OF_STOCK
    assert (works.get("delivery_status"), works.source("delivery_status")) == (M.D_PARTLY, M.SRC_DETAIL)


def test_conflicts_gi_notes_and_reused_articles(works):
    d = works.detail_files[0]
    assert sorted(d.conflict_lines, key=int) == ["23", "24", "25", "33", "34", "35", "36", "37"]
    assert (d.gi_to_make, d.gi_to_reverse) == (4, 1)
    assert d.reused_articles == ["10050004", "10060006", "10060014", "10060027"]
    assert {"line_conflict", "reorders", "gi_notes", "no_vendor", "article_reuse",
            "no_values"} <= codes(works)
    no_vendor = next(f for f in works.flags if f.code == "no_vendor")
    assert "3 open lines" in no_vendor.text and "#30" in no_vendor.text


def test_group_columns_fill_down_within_a_vendor_and_respect_merged_cells(works):
    by_num = {ln.num: ln for ln in works.detail_files[0].lines}
    assert by_num["3"].pr_po == "4500010002"          # same vendor: filled down
    assert by_num["9"].pr_po == "4500010003"          # new vendor: its own value
    assert by_num["10"].sales_order == "3100030001"   # merged block
    assert by_num["19"].pr_po == "4500010004"         # merged block
    assert by_num["23"].pr_po == "4500010009"         # second merged block, same vendor
    assert by_num["20"].pr_po == ""                   # blank merged block means none
    assert by_num["30"].pr_po == "" and by_num["30"].vendor == ""   # vendor is never filled down
    assert by_num["32"].pr_po == ""                   # own stock: no purchase order
    assert by_num["38"].pr_po == ""                   # "-" means none
    assert by_num["35"].quotation == "2025/CON00200" and by_num["35"].vendor == ""
    assert by_num["34"].vendor == "HOME STORE"


def test_two_delivery_note_systems(works):
    by_num = {ln.num: ln for ln in works.detail_files[0].lines}
    assert (by_num["1"].delivery_note, by_num["1"].delivery_note_kind) == ("DN-2025-201", "DN")
    assert (by_num["31"].delivery_note, by_num["31"].delivery_note_kind) == ("7100050001", "SAP")
    assert by_num["20"].delivery_note == ""


# ------------------------------------------------------------------ a differently laid out detail file
def test_links_sheet_and_tolerant_detail_reader(build):
    pf2 = build(links=[["water meters", "Water meters for Lagoon City"]])
    p = find(pf2, "Water meters")
    d = p.detail_files[0]
    assert d.link_reason == "Links sheet" and not pf2.unlinked
    assert [ln.description for ln in d.lines] == [
        "WATER METER 15MM BRASS", "WATER METER 20MM BRASS", "BULK FLOW METER 100MM"]
    assert [ln.status for ln in d.lines] == [M.L_DELIVERED, M.L_PARTIAL, M.L_PENDING]
    assert d.unknown_columns == ["Checked by"] and d.lines[0].extra == {"Checked by": "A.R."}
    assert d.lines[2].site == "Lot 2" and d.lines[2].eta == dt.date(2026, 2, 1)
    assert d.progress.basis == "value" and d.progress.by_value == 35.9
    assert "no_values" not in codes(p)
    # an open line is expected after the due date (13 Jan 2026): at risk
    assert p.get("due_date") == dt.date(2026, 1, 13)
    assert p.status == M.S_AT_RISK and "eta_after_due" in codes(p)


def test_dropdown_choice_is_remembered(build, tmp_path):
    state = StateStore(tmp_path / "state")
    assert [d.name for d in build(state=state).unlinked] == [sample_data.SECOND_DETAIL_NAME]
    state.save_link(sample_data.SECOND_DETAIL_NAME, "Supply of Water meters for Lagoon City")
    again = build(state=StateStore(tmp_path / "state"))      # a new session reads the saved file
    assert not again.unlinked
    assert find(again, "Water meters").detail_files[0].link_reason == "your choice"


# ------------------------------------------------------------------ override layers
def test_correction_overrides_the_value_and_is_labelled(build):
    pf2 = build(corrections=[["12 Units", "contract_value", 8450220.40, "per invoice"]])
    p = find(pf2, "12 Units")
    assert (p.get("contract_value"), p.source("contract_value")) == (8450220.40, M.SRC_CORRECTION)
    assert p.values["contract_value"].note == "per invoice"
    assert not pf2.problems


def test_known_limitation_is_fixed_by_one_correction_row(build):
    pf2 = build(corrections=[["PHASE-II", "delivery_status", "Partly delivered",
                              "signed delivery note pending"]])
    p = find(pf2, "PHASE-II")
    assert (p.get("delivery_status"), p.source("delivery_status")) == (M.D_PARTLY, M.SRC_CORRECTION)
    assert p.status == M.S_LATE


def test_corrections_drive_calculated_values(build):
    pf2 = build(corrections=[
        ["EQUIPMENT SUPPLY- PHASE-I", "delivery days", "60 days", ""],
        ["Crew identity card", "unpaid", "160,000.00", ""],
        ["Crew identity card", "delivery_status", "partial", ""],
        ["Sports flooring", "due_date", "31.12.2025", ""],
        ["cell block", "payment_status", "Paid", ""],
    ])
    phase1 = find(pf2, "EQUIPMENT SUPPLY- PHASE-I")
    assert phase1.get("due_date") == dt.date(2024, 7, 19) and phase1.source("due_date") == M.SRC_CALC
    assert phase1.status == M.S_LATE
    card = find(pf2, "CREW IDENTITY")
    assert card.get("unpaid") == 160000.00 and "unpaid_unclear" not in codes(card)
    assert card.get("delivery_status") == M.D_PARTLY
    flooring = find(pf2, "Sports flooring")
    assert flooring.source("due_date") == M.SRC_CORRECTION and flooring.status == M.S_ON_TRACK
    assert find(pf2, "cell block").get("unpaid") == 0


def test_bad_corrections_are_reported_in_plain_english_not_applied(build):
    pf2 = build(corrections=[
        ["South Atoll Dewatering", "unpaid", 1, ""],              # two projects contain this
        ["No such project", "unpaid", 1, ""],
        ["12 Units", "colour", "blue", ""],
        ["12 Units", "agreement_date", "soon", ""],
        ["Supply and Delivery of HDPE Pipes and Fitting for South Atoll Dewatering",
         "next_action", "Chase payment", ""],                     # exact name is not ambiguous
    ])
    text = " ".join(pf2.problems)
    assert "matches 2 projects" in text and "no project name contains 'No such project'" in text
    assert "'colour' is not a field" in text and "needs a date" in text
    assert len(pf2.problems) == 4
    exact = [p for p in pf2.projects if p.name.endswith("South Atoll Dewatering")][0]
    assert exact.get("next_action") == "Chase payment"
    assert find(pf2, "12 Units").get("agreement_date") == dt.date(2024, 1, 15)


def test_new_columns_beat_notes_and_corrections_beat_columns(build):
    pf2 = build(
        extra_columns={"Agreement date": {"12 Units": "20.01.2024"},
                       "Due date": {"PHASE-I\n": dt.datetime(2026, 3, 1)},
                       "Delivery status": {"PHASE-II": "Partly delivered", "12 Units": "Delivered"},
                       "Next action": {"12 Units": "Hand over last 3 vans"}},
        corrections=[["12 Units", "delivery_status", "In progress", ""]])
    vans = find(pf2, "12 Units")
    assert (vans.get("agreement_date"), vans.source("agreement_date")) == (dt.date(2024, 1, 20), M.SRC_COLUMN)
    assert vans.get("due_date") == dt.date(2024, 4, 4)
    assert (vans.get("delivery_status"), vans.source("delivery_status")) == (M.D_IN_PROGRESS, M.SRC_CORRECTION)
    assert (vans.get("next_action"), vans.source("next_action")) == ("Hand over last 3 vans", M.SRC_COLUMN)
    assert vans.payment_text == "partially cleared"            # unnamed column is still found
    assert find(pf2, "PHASE-II").source("delivery_status") == M.SRC_COLUMN
    phase1 = find(pf2, "EQUIPMENT SUPPLY- PHASE-I")
    assert (phase1.get("due_date"), phase1.source("due_date")) == (dt.date(2026, 3, 1), M.SRC_COLUMN)
    assert phase1.status == M.S_ON_TRACK


def test_corrections_may_live_in_their_own_workbook(cfg, tmp_path):
    folder = sample_data.build_all(tmp_path / "d")
    wb = openpyxl.Workbook()
    wb.active.title = "Corrections"
    wb.active.append(["project", "field", "value", "note"])
    wb.active.append(["12 Units", "next_action", "Call the client", None])
    wb.active.append(["EQUIPMENT SUPPLY- PHASE-I", "delivery_days", None, "left empty on purpose"])
    wb.save(folder / "My corrections.xlsx")
    pf2 = load_portfolio(cfg, AS_OF, folder=str(folder))
    assert find(pf2, "12 Units").get("next_action") == "Call the client"
    assert not pf2.problems
    assert any(f.kind == "corrections" and "1 correction" in f.detail for f in pf2.files)


# ------------------------------------------------------------------ safety and extras
def test_source_files_are_never_modified(cfg, sample_dir):
    before = {f.name: f.read_bytes() for f in sample_dir.iterdir()}
    load_portfolio(cfg, AS_OF, folder=str(sample_dir))
    assert before == {f.name: f.read_bytes() for f in sample_dir.iterdir()}


def test_odd_files_do_not_stop_the_app(cfg, tmp_path):
    folder = sample_data.build_all(tmp_path / "d")
    (folder / "broken.xlsx").write_text("this is not a workbook")
    (folder / "~$Project updates - SAMPLE.xlsx").write_text("lock file")
    other = openpyxl.Workbook()
    other.active.append(["Just", "some", "notes"])
    other.save(folder / "Meeting notes.xlsx")
    pf2 = load_portfolio(cfg, AS_OF, folder=str(folder))
    assert len(pf2.projects) == 23
    kinds = {f.name: f.kind for f in pf2.files}
    assert kinds["broken.xlsx"] == "problem" and kinds["Meeting notes.xlsx"] == "skipped"
    assert not any(name.startswith("~$") for name in kinds)
    assert any("broken.xlsx" in p for p in pf2.problems)


def test_empty_or_missing_folder(cfg, tmp_path):
    assert load_portfolio(cfg, AS_OF, folder=str(tmp_path)).projects == []
    missing = load_portfolio(cfg, AS_OF, folder=str(tmp_path / "nope"))
    assert missing.projects == [] and "does not exist" in missing.problems[0]


def test_what_is_new_since_the_previous_version(cfg, tmp_path):
    folder = sample_data.build_all(tmp_path / "d")
    state = StateStore(tmp_path / "state")
    first = load_portfolio(cfg, AS_OF, state=state, folder=str(folder))
    assert first.new_notes == [] and first.previous_version == ""

    path = folder / sample_data.REGISTER_NAME                 # the user edits the file in Excel
    wb = openpyxl.load_workbook(path)
    ws = wb["Sheet1"]
    row = next(r for r in range(6, 40) if "Solar" in str(ws.cell(r, 1).value))
    ws.cell(row, 5, ws.cell(row, 5).value + "\n1st lot delivered on 08.11.2025")
    ws.cell(40, 1, "Brand new project")
    ws.cell(40, 5, "Plan to submit a proposal")
    wb.save(path)

    second = load_portfolio(cfg, AS_OF, state=state, folder=str(folder),
                            today=dt.date(2025, 11, 11))
    assert [(n.project_name, n.text) for n in second.new_notes] == [
        ("Supply of Solar street lights for Reef Island", "1st lot delivered on 08.11.2025")]
    solar = find(second, "Solar street lights")
    assert [t.text for t in solar.new_entries] == ["1st lot delivered on 08.11.2025"]
    assert find(second, "Brand new project").is_new
    third = load_portfolio(cfg, AS_OF, state=state, folder=str(folder))     # nothing changed
    assert len(third.new_notes) == 1


def test_missing_info_worklist_and_corrections_download(pf):
    assert find(pf, "EQUIPMENT SUPPLY- PHASE-I").missing == ["delivery_days", "unpaid"]
    assert find(pf, "CREW IDENTITY").missing == ["delivery_status", "agreement_date",
                                                 "delivery_days", "unpaid"]
    assert find(pf, "Studio mixer").missing == []             # complete and paid: nothing to chase
    import io
    ws = openpyxl.load_workbook(io.BytesIO(corrections_workbook(pf)))["Corrections"]
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0] == ("project", "field", "value", "note")
    assert ("EQUIPMENT SUPPLY- PHASE-I", "delivery_days") in {(r[0], r[1]) for r in rows[1:]}
    assert all(r[2] is None for r in rows[1:])


def test_downloaded_corrections_file_round_trips(cfg, tmp_path, pf):
    folder = sample_data.build_all(tmp_path / "d")
    (folder / "Corrections.xlsx").write_bytes(corrections_workbook(pf))
    wb = openpyxl.load_workbook(folder / "Corrections.xlsx")
    ws = wb["Corrections"]
    row = next(r for r in range(2, ws.max_row + 1)
               if ws.cell(r, 1).value == "EQUIPMENT SUPPLY- PHASE-I" and ws.cell(r, 2).value == "delivery_days")
    ws.cell(row, 3, 90)
    wb.save(folder / "Corrections.xlsx")
    pf2 = load_portfolio(cfg, AS_OF, folder=str(folder))
    assert not pf2.problems
    assert find(pf2, "EQUIPMENT SUPPLY- PHASE-I").get("due_date") == dt.date(2024, 8, 18)


def test_table_view_has_every_project_and_plain_values(pf):
    rows = table_rows(pf)
    assert len(rows) == 23
    vans = next(r for r in rows if "12 Units" in r["Project"])
    assert vans["Status"] == M.S_LATE and vans["Value"] == 8450120.40 and vans["Unpaid"] == 1450120.40


# ------------------------------------------------------------------ the Excel templates
def test_templates_are_understood_by_the_app(cfg, tmp_path):
    from tools import make_templates
    make_templates.register_template(tmp_path / "Register.xlsx")
    make_templates.detail_template(tmp_path / "30001234 - Harbour office.xlsx")
    make_templates.corrections_template(tmp_path / "Corrections and Links.xlsx")

    wb = openpyxl.load_workbook(tmp_path / "Register.xlsx")
    ws = wb["Projects"]
    head = {c.value: c.column for c in ws[1]}
    for name, value in {"Project ID": "P-2025-001", "Project name": "Harbour office fit-out",
                        "Client": "30001234 Ministry of Harbours", "Project value MVR": 1000,
                        "Agreement date": dt.datetime(2025, 10, 1), "Agreed delivery period": 60,
                        "Delivery status": "In progress", "Payment status": "Not invoiced",
                        "Next action": "Order the doors"}.items():
        ws.cell(2, head[name], value)
    wb.save(tmp_path / "Register.xlsx")

    wb = openpyxl.load_workbook(tmp_path / "30001234 - Harbour office.xlsx")
    ws = wb["Items"]
    head = {c.value: c.column for c in ws[1]}
    rows = [
        {"#": 1, "Description": "DOOR SET", "Quantity": 4, "Delivered Qty": 4, "Unit price": 100,
         "Value": 400, "Line status": "Delivered", "GI note": "NEED TO MAKE GI", "Site / Lot": "Lot 1"},
        {"#": 2, "Description": "FLOOR TILE", "Quantity": 10, "Delivered Qty": 0, "Unit price": 60,
         "Value": 600, "Line status": "Pending", "ETA": dt.datetime(2025, 12, 15), "Remarks": "at port"},
        {"#": 3, "Description": "OLD TILE", "Quantity": 10, "Delivered Qty": 0, "Unit price": 60,
         "Value": 600, "Line status": "Re-ordered"},
    ]
    for r, row in enumerate(rows, start=2):
        for name, value in row.items():
            ws.cell(r, head[name], value)
    wb.save(tmp_path / "30001234 - Harbour office.xlsx")

    pf2 = load_portfolio(cfg, AS_OF, folder=str(tmp_path))
    assert not pf2.problems and len(pf2.projects) == 1
    p = pf2.projects[0]
    assert p.get("project_id") == "P-2025-001"
    assert p.source("agreement_date") == M.SRC_COLUMN and p.get("due_date") == dt.date(2025, 11, 30)
    assert p.get("payment_status") == M.P_NOT_INVOICED and p.get("next_action") == "Order the doors"
    d = p.detail_files[0]
    assert d.link_reason == "customer code 30001234"
    assert [ln.status for ln in d.lines] == [M.L_DELIVERED, M.L_PENDING, M.L_REORDERED]
    assert d.gi_to_make == 1 and d.lines[0].site == "Lot 1"
    assert d.progress.basis == "value" and d.progress.by_value == 40.0
    assert p.source("delivery_status") == M.SRC_COLUMN          # the typed column beats the detail file
    assert p.status == M.S_AT_RISK and "eta_after_due" in codes(p)
