import datetime as dt

from projectdash import textnorm as T


def test_line_breaks_and_excel_escape_become_separators():
    text = "04.12.2023 - Proposal_x000B_Agreement Signed\x0bPR Created\nDelivered"
    assert T.fragments(text) == ["04.12.2023 - Proposal", "Agreement Signed", "PR Created", "Delivered"]
    assert T.normalise(text) == "04.12.2023 - Proposal | Agreement Signed | PR Created | Delivered"


def test_double_spaces_inside_a_line_are_kept_together_when_real_breaks_exist():
    assert T.fragments("Payment received\nBalance  - 300,000.00") == [
        "Payment received", "Balance - 300,000.00"]


def test_double_spaces_split_only_when_there_is_no_line_break():
    assert T.fragments("Agreement signed  PR created   Delivered") == [
        "Agreement signed", "PR created", "Delivered"]


def test_tabs_separate_and_blank_cells_are_empty():
    assert T.fragments("6100012001\t   300,000.05") == ["6100012001", "300,000.05"]
    assert T.fragments(None) == [] and T.fragments("   ") == []
    assert T.fragments(3100009001) == ["3100009001"]


def test_dates_in_text():
    found = [d for _s, _e, d in T.find_dates(
        "18.12.2023 x 10th June 2024 x 22 July 2024 x 31st Dec 2024 x 8TH SEPT 2025")]
    assert found == [dt.date(2023, 12, 18), dt.date(2024, 6, 10), dt.date(2024, 7, 22),
                     dt.date(2024, 12, 31), dt.date(2025, 9, 8)]


def test_dates_without_a_year_are_ignored():
    assert T.find_dates("ETA-9th May, sample sent 14-09, REQUESTED ON 8TH SEPT") == []
    assert T.find_dates("Agreement # 70-PA/CON-P/2024/415") == []
    assert T.find_dates("32.13.2024") == []


def test_amounts_are_not_confused_with_dates():
    assert T.find_amount("dispatched on 25.07.2024") is None
    assert T.find_amount("on 10.10.2024 (2,000,000.25)") == 2000000.25
    assert T.find_amount("MVR-900,000.00") == 900000.00
    assert T.find_amount("Balace - 160000.") is None


def test_cells_as_dates():
    assert T.to_date("18.12.2023") == dt.date(2023, 12, 18)
    assert T.to_date(45291) == dt.date(2023, 12, 31)            # Excel serial number
    assert T.to_date(dt.datetime(2024, 3, 1, 9, 30)) == dt.date(2024, 3, 1)
    assert T.to_date("2024-03-01") == dt.date(2024, 3, 1)
    assert T.to_date("01/03/2024") == dt.date(2024, 3, 1)
    assert T.to_date("Completed") is None and T.to_date(None) is None


def test_numbers_are_rounded_to_drop_float_artifacts():
    assert T.to_number(4200300.5999999996) == 4200300.60
    assert T.to_number("MVR 1,250,300.60") == 1250300.60
    assert T.to_number("n/a") is None
    assert T.to_int("75 days") == 75 and T.to_int("Completed") is None


def test_match_key_ignores_case_and_spacing():
    assert T.match_key("Procurement  ( 12 Units) vans\n") == "procurement ( 12 units) vans"
    assert T.is_blank("-") and T.is_blank(None) and not T.is_blank("DN-2025-201")
