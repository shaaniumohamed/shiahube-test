"""Builds made-up sample workbooks that copy the quirks of real hand-kept files.

Every name, number and amount here is invented. The files are used by the
automated tests and by the app's demo mode (when the data folder is empty).

Run ``python tools/sample_data.py`` to (re)create the ``sample_data`` folder.
"""
from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

REGISTER_NAME = "Project updates - SAMPLE.xlsx"
DETAIL_NAME = "20004567 - DEPARTMENT OF PUBLIC WORKS.xlsx"
SECOND_DETAIL_NAME = "Water meters order tracker.xlsx"

# (name, client, value, request date, status, order type, PR number, PR date,
#  delivery period, SO number, remarks, payment column)
PROJECTS = [
    ("Procurement  ( 12 Units) vans\n", "Ministry of Harbours ", 8450120.3999999994, "04.12.2023",
     "04.12.2023-Proposal submitted for 12 units; 11.12.2023 -  Project awarded_x000B_"
     "15.01.2024 - Agreement Signed_x000B_PR Created,_x000B_20.12.2023 - submitted performance "
     "guarantee\nVehicle delivered.\nInv-6100003311 - dispatched on 20.07.2024\n"
     "2 Van- Vehicle garage- Camera fixing\n12 cover / spare wheel - Shipped-ETA not received yet",
     "FOREIGN", None, None, "75 days", None,
     "1st Lot\n5- vans Handovered\nAnnual fee, Roadworthiness, Insurance completed.\n2nd Lot\n"
     "4- vans received, registration processing\n3rd Lot\nETA-9th May\n"
     "Payment received - 7,000,000.00\nBalance  - 1,450,120.40",
     "partially cleared"),
    ("Procurement  of   Studio mixer _Mixed HD SD Playback unit\n", "Ministry of Culture", 410500,
     "20.12.2023",
     "28.12.2023-Proposal submitted for 2 units;  \n15.01.2023 - submitted performance guarantee\n"
     "22.01.2024 - Agreement draft received\nWaiting for legal comment\nCOMPLETED-",
     "Local", None, None, None, None,
     "Completed.\nInvoice dispatched on 28.04.2024\nINV-921000111", None),
    ("Procurement of Patrol boat", "Coast Authority", None, "22.01.2024",
     "Plan to propose suitable  models to  identify their need with engineering team. Since the "
     "boat is required for dual purpose, some modification might be needed.",
     None, None, None, None, None, None, None),
    ("Replacement of Archive hall roofing", "Culture Ministry", None, "22.01.2023",
     "Held a meeting with ministry & procurement team. We agreed to conduct a separate meeting "
     "to identify the business opportunities.",
     None, None, None, None, None, None, None),
    ("Supply and Delivery of HDPE Pipes and Fitting for North Harbour Outfall works", "IRC",
     1250300.6, None, "Agreement no: (AGR)IRC/60/2024", "Foreign", None, None, None, 3100001001,
     "Completed.\nInvoice dispatched on 11.07.2024\nINV-6100001501", None),
    ("Health Awareness Day Event", "Ministry of Wellbeing", 150000, None, "PO-1163240999",
     "Local", None, None, "Completed", 5100272999,
     "Completed.\nInvoice dispatched on 15.05.2024\nINV-921000222", None),
    ("Procurement of Survey Equipments", "Reef Agency", 900000, None,
     "Final draft agreement shared with agency on 11.06.2024\nAgreement #(AGR)508-RA/60/2024/2\n"
     "Contract signed 27th June 2024\nPR 0030000601 has been created \nSales order-3100002001\n"
     "Performance Guarantee submitted.\nDelivered- \nInv dispatched on - 25.08.2024\n"
     "INV-6100005001 - MVR-900,000.00",
     "Local", None, None, None, None, "6100005001 (900,000.00)", None),
    ("EQUIPMENT SUPPLY- PHASE-I", "National Broadcaster", 9100200.98, None,
     "Agreement signed on 20.05.2024\nAgreement # 60-LA-CON-L-2024-400\n"
     "PR-3000234001 created on 21.05.2024\n1st Lot- Gateway- items delivered on 26.08.2024- "
     "signed delivery note received \nGR-requsted for delivered items",
     "FOREIGN", None, None, None, None, None, "NOT CLEARED"),
    ("Supply and Delivery of HDPE Pipes and Fitting for East Lagoon Road", "IRC", 500000, None,
     "Agreement Signed on 10th June 2024\nAgreement # (AGR)IRC/60/2024/03\nPO-4510000201 \n"
     "Sales order:3100001002\nPerformance Guarantee submitted.\nDELIVERED- INVOICE PENDING\n"
     "REQUESTED GR & GI",
     "FOREIGN", None, None, None, None,
     "6100007001 (500,000.00)\npayment received - 200,000.00 on 31st Dec 2024\n"
     "Balance  - 300,000.00", "partially cleared"),
    ("Supply and Delivery of HDPE Pipes and Fitting for South Atoll Dewatering", "IRC",
     4200300.5999999996, None,
     "Agreement # (AGR)IRC/60/2024/05\nSinged on 27th June 2024\nPO- 4510000301 created \n"
     "Sales order-3100003001\nPerformance Guarantee submitted.\nDuty letter Received\n"
     "All the pipes delivered on 18.07.2024\nRemaining accessories - Delivered on 01.09.2024\n"
     "Invoice (Pipes) - 6100006101 - Mvr 3,000,100.00 (Dispatched on 01.09.2024)\n"
     "Invoice (Acc) - 6100006102 - 1,200,200.60 (Dispatched on 08.09.2024)",
     "FOREIGN", None, None, None, None,
     "Invoice (Pipes) - 6100006101 - Mvr 3,000,100.00 (Dispatched on 01.09.2024)\n"
     "Invoice (Acc) - 6100006102 - 1,200,200.60 (Dispatched on 08.09.2024)", "NOT CLEARED"),
    ("PRODUCTION AND PERSONALIZATION OF\nCREW IDENTITY CARD\n(incl. delivery)",
     "MINISTRY OF PORTS", 240000, None,
     "Quotation Number: 2024/CON0070\nAgreement signed\nAgreement # 70-PA/CON-P/2024/415\n"
     "Sales order - 3100003501\nInvoice dispatched on - 13.08.2024\nINV-6100004001 - MVR-80,000.00",
     "FOREIGN", None, None, None, None,
     "Invoice dispatched on - 13.08.2024\nINV-6100004001 - MVR-80,000.00\nBalace - 160000.",
     "partially cleared"),
    ("EQUIPMENT SUPPLY- PHASE-II", "National Broadcaster", 11500700.13, None,
     "QTN-2024/CON0312 - initial offer submitted for approval on 08th July 2024\n"
     "Amended quot including battery prices submitted for approval on 21st July 2024\n"
     "New quotation submitted for approval on 27.08.2024\n3100010001",
     "FOREIGN", None, None, None, None,
     "PROJECT TIME LINE:\nSigned date:02.10.2024\nPO date: (4510001001) 07.10.2024\n"
     "Invoice 6100015001 -1,100,000.50\nReceived Advance payment on 10.10.2024 (2,000,000.25) \n"
     "DURATION- 35 Days\nUnit delivered on 05.11.2024",
     "partially cleared\n(Signed delivery note pending)"),
    ("Supply & Delivery of Sports flooring for Site A, Site B & Site C project", "IRC",
     6100500.16, None,
     "Agreement number# (AGR)IRC/60/2024/07\nPR Created\n"
     "Site A - 0030002001 / 3100005001 (mvr 3,000,000.04)\n"
     "Site B - 0030002002 / 3100005002 (mvr 2,000,000.08)\n"
     "Site C - 0030002003 / 3100005003 (mvr 1,100,500.04)\nAgreement Signed on 18.08.2024\n"
     "PG submitted\nSample submitted for approval - 14-09",
     "Foreign", None, None, None, " 3100005001\n3100005002\n 3100005003",
     "ONGOING\nsales order need to be amended",
     "not invoice\n(Site C - 2025-031)\n(Site B - 2025-032)"),
    ("Supply and Delivery of HDPE Pipes and Fitting for West Island Major Road Project", "IRC",
     400100.24, None,
     "Draft Agreement (AGR)IRC/60/2024/08\nCustomer PO-IRC-2024-003001\n"
     "Shared with legal for comment on 22.08.2024\nSales order-3100005901",
     "Foreign", None, None, None, 3100005901,
     "Schedule to clear on 28.11.2024\n6100016001 (MVR 400,100.24)", "NOT CLEARED"),
    ("Supply and Delivery of HDPE Pipes and Fitting for South Atoll Dewatering - Additional",
     "IRC", 420000.6, None,
     "Purchase order received on-22.08.2024\nPO-IRC-2024-003002\nPO-4510001002\n"
     "Sales order-3100005701\nitem delivered, Shortage 40 EA Bolt",
     "Foreign", None, None, None, 3100005701,
     "INVOICE DISPATCHED ON 24.11.2024\n6100014001 - MVR-414,000.92\n", "NOT CLEARED"),
    ("City Library Renovation", "Coral City Council", None, None,
     "Final draft agreement shared on 28.08.2024\nDue to outstanding payments Finance is waiting "
     "for the outstanding update to allocate credit \nCredit approved by finance \n"
     "Agreement signing process",
     "Local", None, None, None, None, None, None),
    ("Training centre cell block", "National Guard", 2189001.96, None, 3100009001,
     "Local", None, None, None, None,
     "6100012001\t            300,000.05\n6100012002\t              19,000.00\n"
     "6100012003\t         1,200,000.76\n6100012004\t              50,000.00\n"
     "6100012005\t            500,000.27\n6100012006\t            120,000.88 \n"
     "Invoice has been posted to Finance portal", "NOT CLEARED"),
    ("Supply and Delivery of UPVC Pipes for West Island", "IRC", 1400500.4, None,
     "Agreement signed on-27.10.2024\nAGR-REF- (AGR)IRC/60/2024/10 \nSales Order-3100011001\n"
     "PG Submitted",
     "FOREIGN", 30004001, "28.10.2024", "45 Days", 3100011001,
     "DELIVERED\n(Delivery note- DN-2025-044\nInvoice dispatched on 05.02.2025\n"
     "INV-6100022001 - MVR-1,330,000.80", "COMPLETED"),
    ("Supply and Delivery of UPVC Pipes for Long Island", "IRC", 2500000.04, None,
     "Agreement signed on-27.10.2024\nAGR-REF- (AGR)IRC/60/2024/09\nSales Order-3100011002 \n"
     "PG submitted",
     "FOREIGN", 30004002, "28.10.2024", "45 days", 3100011002,
     "6100026001 (MVR 2,500,000.04)", "need to dispatched"),
    ("20004567 - DEPARTMENT OF PUBLIC WORKS ", "WORKS COUNCIL", 1900400.58, None,
     "Agreement Signed on- 25.11.2024\nAgreement Reference-60-LA/CON-L/2024/900",
     "Local", "30005001\n30005002", None, "30 Days", 3100013001,
     "6100019001 - 800,000.38\n6100020001 - 200,000.80", "NOT CLEARED"),
    ("Supply of Solar street lights for Reef Island", "Northern Utilities", 3200000, "01.10.2025",
     "Agreement signed on 20.10.2025\nPR created on 22.10.2025\n"
     "Shipment confirmed by supplier on 02.11.2025",
     "FOREIGN", None, None, "30 days", None, "ONGOING", None),
    ("Supply of Water meters for Lagoon City", "Northern Utilities", 780000, "20.09.2025",
     "Agreement signed on 15.10.2025\nPO-4510009001 created on 18.10.2025\n"
     "Supplier confirmed production on 30.10.2025",
     "FOREIGN", None, None, "90 days", None, "ONGOING", None),
    ("Supply of LED floodlights for the Stadium", "Coral City Council", 1650000, "15.09.2025",
     "Agreement signed on 01.10.2025\nPR created on 03.10.2025\nGoods under production",
     "Local", None, None, "120 days", None, "ONGOING\nWeekly update received on 05.11.2025", None),
]
HIDDEN_PROJECT = "City Library Renovation"

INVOICE_ROWS = [
    # number, agreement ref, PO, amount, project, dispatched, customer, payment status
    (6100003311, "(AGR)27-H/60/2024/3", "-", 8450220.4, "Supply of 12 vans", "20.07.2024",
     "MINISTRY OF HARBOURS", "24.08.2024"),
    (6100005001, "(AGR)508-RA/60/2024/2", "-", 900000, "Survey Equipment", "25.08.2024",
     "Reef Agency", "Cleared"),
    (921000111, "(AGR) 318-C 2/60/2024/4", "-", 410500, "Studio mixer", "28.04.2024",
     "Ministry of Culture", "Cleared"),
    (6100014999, "AGR-60-LA/CON-L/2024/400", "-", 9100200.98,
     "Supply and Delivery of equipment phase-1", "19.11.2024", "National Broadcaster",
     "Installment basis,\n3 months Grace"),
    (6100019001, "60-LA/CON-L/2024/900", 1556240001, 800000.38,
     "Supply and Delivery of materials for office building.", "30.12.2024", "WORKS COUNCIL",
     "Cleared"),
    (6100014001, "-", "PO-IRC-2024-003002", 414100.92, "South Atoll Dewatering-Additional",
     "24.11.2024", "IRC", "19.02.2025"),
]

REGISTER_HEADERS = ["Project name", "Client", "Projct value MVR", "Request date", "Status",
                    "Order Type", "PR Number", "PR Date", "Agreed delivery period", "SO number",
                    "REMARKS"]


def build_register(path: Path, corrections: list | None = None, links: list | None = None,
                   extra_columns: dict[str, dict[str, object]] | None = None) -> Path:
    """Write the sample register.

    ``corrections`` rows are (project, field, value, note); ``links`` rows are
    (file, project). ``extra_columns`` maps a new header (e.g. "Due date") to
    {project name text: value} to test the optional columns.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws["A3"] = "Ongoing Project updates"
    headers = list(REGISTER_HEADERS)
    for c, h in enumerate(headers, start=1):
        ws.cell(5, c, h)
    extra_columns = extra_columns or {}
    extra_start = len(headers) + 2            # column L stays without a header (payment status)
    for i, h in enumerate(extra_columns):
        ws.cell(5, extra_start + i, h)
    row = 6
    for p in PROJECTS:
        for c, value in enumerate(p[:11], start=1):
            if value is not None:
                ws.cell(row, c, value)
        if p[11] is not None:
            ws.cell(row, 12, p[11])
        for i, (h, values) in enumerate(extra_columns.items()):
            for text, value in values.items():
                if (p[0] + "\n").lower().endswith(text.lower()) or \
                        ("\n" not in text and text.lower() in p[0].lower()):
                    ws.cell(row, extra_start + i, value)
        if p[0] == HIDDEN_PROJECT:
            ws.row_dimensions[row].hidden = True
        row += 1
    ws.cell(row, 3, f"=SUM(C6:C{row - 1})")
    ws.cell(row, 4, "project value")
    for i, text in enumerate(["Ongoing project", "Invoiced value", "Payment not received",
                              "Payment received"], start=1):
        ws.cell(row + i, 4, text)

    s2 = wb.create_sheet("Sheet2")
    s2.append(["Project name", "Client", "Projct value MVR", "Status"])
    for p in PROJECTS[:8]:
        s2.append([p[0], p[1], p[2], "Completed"])

    inv = wb.create_sheet("INVOICE")
    inv.append(["Invoice Number", "Agreement Ref", "Purchase order Number", "Amount MVR",
                "Project", "Dispatched date", "Customer", "Payment Status"])
    for r in INVOICE_ROWS:
        inv.append(list(r))

    if corrections is not None:
        cs = wb.create_sheet("Corrections")
        cs.append(["project", "field", "value", "note"])
        for r in corrections:
            cs.append(list(r))
    if links is not None:
        ls = wb.create_sheet("Links")
        ls.append(["file", "project"])
        for r in links:
            ls.append(list(r))
    wb.save(path)
    return path


DETAIL_HEADERS = ["#", "Customer Name", "Article", "Description", "Unit", "Quantity",
                  "Delivered Qty", "Balance Qty", "Vendor", "Vendor Qtn No", "Quotation",
                  "SAP Quotation", "Sales Order", "PR / PO", "Client PO", "Delivery Note",
                  "Invoice", "Value", "Dispatched date", "Remarks"]
CUSTOMER = "20004567 - DEPARTMENT OF PUBLIC WORKS "
QTN, SAPQ, SO, CPO = "2025/CON00200", 4200080001, 3100030001, 1556250001

# Each line: (#, article, description, unit, qty, delivered, vendor, vendor quote,
#             quotation, sap quotation, sales order, pr/po, delivery note, invoice, remark, note)
# Group columns are only typed on the first row of a group, as in real files.
_ = None
DETAIL_LINES = [
    (1, 10060001, "NETWORK CABLE - 305 MTR", "ROLL", 9, 9, "CABLE DEPOT", "#37001", QTN, SAPQ, SO, 4500010001, "DN-2025-201", _, "Delivered", _),
    (2, 10060002, "CEMENT BOARD 4'X8'X6MM ", "PCS", 130, 130, "BUILD MART", "BM/25/QUOT/100", QTN, SAPQ, SO, 4500010002, "DN-2025-202", _, "Delivered", _),
    (3, 10060003, 'SELF DRILLING SCREW 2" (50MM)', "PCS", 4000, 4000, "BUILD MART", "BM/25/QUOT/100", _, _, _, _, "DN-2025-202", _, "Delivered", _),
    (4, 10060004, "TILE ADHESIVE - BAG X 20KG ", "BAG", 50, 50, "BUILD MART", "BM/25/QUOT/100", _, _, _, _, "DN-2025-202", _, "Delivered", "NEED TO MAKE GI"),
    (5, 10050004, "CEILING EXHAUST FAN, 8''", "PCS", 3, 3, "BUILD MART", "BM/25/QUOT/100", _, _, _, _, "DN-2025-202", _, "Delivered", _),
    (6, 10060006, 'PVC ELBOW 90* - 4" ', "PCS", 6, 6, "BUILD MART", "BM/25/QUOT/100", _, _, _, _, "DN-2025-202", _, "Delivered", _),
    (7, 10060006, 'PVC TEE - 4" ', "PCS", 5, 5, "BUILD MART", "BM/25/QUOT/100", _, _, _, _, "DN-2025-202", _, "Delivered", _),
    (8, 10060008, 'PVC PIPE 3" ', "EA", 8, 8, "BUILD MART", "BM/25/QUOT/100", _, _, _, _, "DN-2025-202", _, "Delivered", _),
    (9, 10060009, "BLACK SCREW, 1 1/2 INCH ", "EA", 4500, 4500, "STEEL WORKS", "#398001", QTN, SAPQ, SO, 4500010003, "DN-2025-201", _, "Delivered", _),
    (10, 10060010, "ROOFING SCREW, 2 INCH", "EA", 2000, 2000, "STEEL WORKS", "#398001", _, _, _, _, "DN-2025-201", _, "Delivered", _),
    (11, 10060011, "WALL PLUG, 8 MM X 50 MM", "EA", 1000, 1000, "STEEL WORKS", "#398001", _, _, _, _, "DN-2025-201", _, "Delivered", _),
    (12, 10060012, "PIPE CLAMP, 1 1/2 INCH ", "EA", 1000, 1000, "STEEL WORKS", "#398001", _, _, _, _, "DN-2025-201", _, "Delivered", "NEED TO MAKE GI"),
    (13, 10060013, "SURFACE MOUNT BOX, 1 GANG", "EA", 83, 83, "STEEL WORKS", "#398001", _, _, _, _, "DN-2025-201", _, "Delivered", _),
    (14, 10060014, "FLEXIBLE CONDUIT PIPE, 25 MM X 50 MTR", "ROLL", 11, 11, "STEEL WORKS", "#398001", _, _, _, _, "DN-2025-201", _, "Delivered", _),
    (15, 10060014, "FLEXIBLE CONDUIT PIPE, 32 MM X 25 MTR", "ROLL", 1, 1, "STEEL WORKS", "#398001", _, _, _, _, "DN-2025-201", _, "Delivered", _),
    (16, 10060014, "FLEXIBLE CONDUIT PIPE, 20 MM X 50 MTR", "ROLL", 11, 11, "STEEL WORKS", "#398001", _, _, _, _, "DN-2025-201", _, "Delivered", _),
    (17, 10060017, "GYPSUM BOARD 9MM 4 X 8 ", "PCS", 130, 130, "TIMBER YARD", "E-52001/2025", QTN, SAPQ, SO, 4500010004, "DN-2025-201", _, "Delivered", _),
    (18, 10050001, "WALL PUTTY 28KG DRUM ", "CAN", 20, 0, "TIMBER YARD", "E-52001/2025", _, _, _, _, "DN-2025-201", _, "Out of Stock", _),
    (19, 10050002, "GYPSUM JOINT TAPE 2 X 90M ", "PCS", 10, 3, "TIMBER YARD", "E-52001/2025", _, _, _, _, "DN-2025-201", _, "3 ea Delivered", "NEED TO MAKE GI"),
    (21, 10060021, "SINGLE BASIN FAUCET", "PCS", 3, 3, "TIMBER YARD", "E-52001/2025", _, _, _, _, "DN-2025-201", _, "Delivered", _),
    (22, 10060022, "PVC PIPE CLASS 5.0 BLUE 1 1/4 ", "EA", 20, 20, "TIMBER YARD", "E-52001/2025", _, _, _, _, "DN-2025-201", _, "Delivered", "NEED TO MAKE GI"),
    (24, 10060024, "PVC VALVE PLUG BLUE / 1/2 ", "EA", 15, 15, "TIMBER YARD", "E-52001/2025", _, _, SO, 4500010009, "DN-2025-205", _, "pending", _),
    (23, 10060023, "PVC TS TEE BLUE / 1/2 ", "EA", 15, 15, "TIMBER YARD", "E-52001/2025", _, _, _, _, "DN-2025-205", _, "pending", _),
    (25, 10060025, "PVC TS ELBOW BLUE / 1/2 ", "EA", 15, 15, "TIMBER YARD", "E-52001/2025", _, _, _, _, "DN-2025-205", _, "pending", _),
    (20, 10050003, "PVC PIPE CLASS 5.0 BLUE 1/2", "EA", 5, 0, "TIMBER YARD", "E-52001/2025", _, _, SO, _, "-", _, "Out of Stock", _),
    (26, 10050004, "CYCLE (ORBIT) FAN WITH REMOTE 18 ", "PCS", 2, 0, "TIMBER YARD", "E-52001/2025", _, _, _, _, "-", _, "Out of Stock", "NEED TO REVERSE GI"),
    (27, 10060027, "DOOR SET (W 2700MM X L 2100MM) TIMBER LAMINATED", "EA", 1, 1, "DOOR STUDIO", "DS/QT/2025/0360", QTN, SAPQ, SO, 4500010005, "DN-2025-203", _, "delivered", _),
    (28, 10060027, "DOOR SET (W 955MM X L 2100MM) TIMBER LAMINATED", "EA", 3, 3, "DOOR STUDIO", "DS/QT/2025/0360", _, _, _, _, "DN-2025-203", _, "delivered", _),
    (29, 10060029, "PARQUET FLOOR TILE (18 X 122CM)", "EA", 2200, 2200, "DOOR STUDIO", "DS/QT/2025/0360", _, _, _, _, "DN-2025-203", _, "delivered", _),
    (30, 10050005, "UNTREATED PINE WOOD 2\" X 6\" X 14'", "EA", 130, 0, _, _, _, _, _, _, "-", _, "Out of stock", _),
    (31, 10070031, "INVERTER AC 12BTU", "EA", 3, 3, "STO", _, 4200080002, 4200080002, SO, _, 7100050001, 6100040001, "Delivered", _),
    (32, 40000032, 'COPPER PIPE 1/4"-50FT (FT)', "FT", 200, 200, "STO", _, _, _, _, _, 7100050001, _, "Delivered", _),
    (37, 10070037, "EASY WASH PAINT 5LTR - WHITE", "EA", 36, 36, "STO", _, 4200080003, 4200080003, SO, "-", "DN-2025-206", _, "pending", "New shipment eta 15th Nov"),
    (38, 10070038, '7" ROLLER HANDLE CHROME', "EA", 7, 0, "STO", _, _, _, _, _, "-", _, "pending", "New shipment eta 15th Nov"),
    (33, 10050002, "GYPSUM JOINT TAPE 2 X 90M ", "PCS", 7, 7, "STEEL WORKS", "#407001", QTN, 4200080003, SO, 4500010010, "DN-2025-206", _, "pending", _),
    (34, 10050001, "WALL PUTTY 28KG DRUM ", "CAN", 20, 20, "HOME STORE ", "#660", QTN, 4200080003, SO, 4500010011, "DN-2025-207", _, "pending", _),
    (35, 10050003, "PVC PIPE CLASS 5.0 BLUE 1/2", "EA", 5, 5, _, _, _, _, _, _, "DN-2025-207", _, "pending", _),
    (36, 10050004, "ORBIT FAN ", "PCS", 2, 2, _, _, _, _, _, _, "DN-2025-207", _, "pending", _),
]
# Merged blocks as (column letter, first #, last #) by position in the list above.
DETAIL_MERGES = [("M", 9, 16), ("K", 17, 26), ("N", 17, 22), ("N", 24, 25), ("N", 20, 26),
                 ("N", 37, 38), ("K", 34, 36), ("M", 34, 36)]


def build_detail(path: Path) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    for c, h in enumerate(DETAIL_HEADERS, start=1):
        ws.cell(4, c, h)
    row_of: dict[int, int] = {}
    for i, ln in enumerate(DETAIL_LINES):
        r = 5 + i
        num, article, desc, unit, qty, delivered, vendor, vq, q, sq, so, po, dn, inv, remark, note = ln
        row_of[num] = r
        values = [num, CUSTOMER, article, desc, unit, qty, delivered, f"=F{r}-G{r}", vendor, vq,
                  q, sq, so, po, CPO, dn, inv, None, None, remark, note]
        for c, value in enumerate(values, start=1):
            if value is not None:
                ws.cell(r, c, value)
    for col, first, last in DETAIL_MERGES:
        ws.merge_cells(f"{col}{row_of[first]}:{col}{row_of[last]}")
    ws.auto_filter.ref = f"A4:T{4 + len(DETAIL_LINES)}"
    wb.save(path)
    return path


def build_second_detail(path: Path) -> Path:
    """A detail file laid out differently: other header names, prices and ETAs filled in."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Tracker"
    ws["A1"] = "Water meters - order tracker"
    ws.append(["S/N", "Item", "UOM", "Qty", "Delivered", "Supplier", "Unit Price", "ETA",
               "Lot", "Status", "Checked by"])
    ws.append([1, "WATER METER 15MM BRASS", "EA", 100, 100, "METER WORLD", 2000, None, "Lot 1",
               "Delivered", "A.R."])
    ws.append([2, "WATER METER 20MM BRASS", "EA", 50, 20, "METER WORLD", 4000, "20.12.2025",
               "Lot 1", None, "A.R."])
    ws.append([3, "BULK FLOW METER 100MM", "EA", 10, 0, "FLOW SYSTEMS", 38000, "01.02.2026",
               "Lot 2", "pending", None])
    ws.append([None, "TOTAL", None, 160, 120, None, None, None, None, None, None])
    wb.save(path)
    return path


def build_all(folder: Path, corrections: list | None = None, links: list | None = None,
              extra_columns: dict | None = None) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    build_register(folder / REGISTER_NAME, corrections, links, extra_columns)
    build_detail(folder / DETAIL_NAME)
    build_second_detail(folder / SECOND_DETAIL_NAME)
    return folder


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "sample_data"
    build_all(target)
    print(f"Sample files written to {target}")
