from projectdash.excel import Sheet, find_header_row, map_headers
from projectdash.sources.detail import HEADERS as DETAIL
from projectdash.sources.register import HEADERS as REGISTER


def test_register_headers_are_matched_by_name_with_typos():
    cells = ["Project name", "Client", "Projct value MVR", "Request date", "Status", "Order Type",
             "PR Number", "PR Date", "Agreed delivery period", "SO number", "REMARKS", None,
             "Delivery status", "Due date", "Agreement date", "Next action"]
    cols = map_headers(cells, REGISTER)
    assert cols == {"name": 1, "client": 2, "value": 3, "request_date": 4, "status": 5,
                    "order_type": 6, "pr_number": 7, "pr_date": 8, "delivery_period": 9,
                    "so_number": 10, "remarks": 11, "delivery_status": 13, "due_date": 14,
                    "agreement_date": 15, "next_action": 16}


def test_column_order_does_not_matter():
    cols = map_headers(["Remarks", "Status", "Client", "Project Name"], REGISTER)
    assert (cols["remarks"], cols["status"], cols["client"], cols["name"]) == (1, 2, 3, 4)


def test_detail_headers():
    cells = ["#", "Customer Name", "Article", "Description", "Unit", "Quantity", "Delivered Qty",
             "Balance Qty", "Vendor", "Vendor Qtn No", "Quotation", "SAP Quotation", "Sales Order",
             "PR / PO", "Client PO", "Delivery Note", "Invoice", "Value", "Dispatched date", "Remarks"]
    cols = map_headers(cells, DETAIL)
    assert [cols[k] for k in ("num", "customer", "article", "description", "unit", "qty",
                              "delivered", "balance", "vendor", "vendor_quote", "quotation",
                              "sap_quotation", "sales_order", "pr_po", "client_po",
                              "delivery_note", "invoice", "value", "dispatched", "remarks")] \
        == list(range(1, 21))


def test_detail_headers_spelled_differently():
    cols = map_headers(["S/N", "Item", "UOM", "Qty", "Delivered", "Supplier", "Unit Price", "ETA",
                        "Lot", "Status", "Checked by"], DETAIL)
    assert cols == {"num": 1, "description": 2, "unit": 3, "qty": 4, "delivered": 5, "vendor": 6,
                    "unit_price": 7, "eta": 8, "site": 9, "remarks": 10}


def test_header_row_is_found_below_a_title():
    sheet = Sheet("S", [[], [], ["Ongoing Project updates"], [],
                        ["Project name", "Client", "Status"], ["A project", "X", "ongoing"]])
    assert find_header_row(sheet, [["project name"]]) == 5
    assert find_header_row(sheet, [["description"], ["quantity"]]) is None
