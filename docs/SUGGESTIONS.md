# Suggestions: making the data easier, without redoing the old files

These come from what the app found when reading the real files. Nothing here is required:
the dashboard works on the files as they are. Each suggestion says what it would unlock.

The guiding rule: **leave history alone, fix only what matters through Corrections, and type
new information in a slightly more regular way.**

---

## 1. The five changes with the biggest payoff

| # | Change | Effort | What you get |
|---|---|---|---|
| 1 | Fill in **Agreed delivery period** (days) for every signed project | One number per project | Due dates, "Late" and "At risk" warnings. Today most projects cannot be checked for lateness because this one number is missing. |
| 2 | Give the **payment column a header** ("Payment status") and pick from a fixed list | Rename one cell | No more guessing from wording such as "need to dispatched". |
| 3 | Add a **Delivery status** column with four choices | One drop-down per project | The app stops inferring delivery from the diary text, which is where most misreadings come from. |
| 4 | Start every new diary line **with the date** (`05.11.2025 - 1st lot delivered`) | A habit | A reliable timeline, "last activity", and the "what's new" feed. |
| 5 | Put a **unit price** (or value) on detail-file lines | One column | Progress measured by value, not by counting lines, so a missing bolt no longer weighs the same as a missing generator. |

The `templates/` folder has Excel files with these columns and drop-down lists already set up.

---

## 2. Data format going forward

### Register (master list)

Keep your sheet. Add these columns anywhere; the app finds them by header name.

| Column | Type | Why |
|---|---|---|
| **Project ID** | short code you never change, e.g. `P-2025-014` | Today projects are matched by name. Several names are nearly identical (a project and its "- Additional" phase; "Phase-I" and "Phase-II"), and a renamed project loses its corrections. An ID removes that risk. |
| **Agreement date** | real date | Today it is read from sentences like "Agreement signed on-…". |
| **Agreed delivery period** | number of days | See change 1. |
| **Due date** | real date | Only when it is not signing date + days (extensions, phased deliveries). |
| **Delivery status** | Not started / In progress / Partly delivered / Delivered | See change 3. |
| **Payment status** | Unpaid / Partly paid / Invoice not sent / Not invoiced / Paid | See change 2. |
| **Next action** | a few words | Shown at the top of the project page. |

General habits:

- **One fact per cell where it is cheap.** The diary can stay free text, but numbers you want
  totalled (contract value, amount received, balance) are safer in their own cells.
- **Real dates, not typed text.** `18.12.2023` typed as text works, but a real Excel date can
  never be mistyped into an impossible date. The app flagged a date that was probably typed
  with the wrong year.
- **Don't use a column for a second purpose.** A status cell holding only a Sales Order
  number, or a delivery-period cell saying "Completed", is read as "nothing here".
- **Keep legend and total rows out of the table**, or leave their project name empty as now.

### Invoices

The INVOICE sheet is already the cleanest part of the workbook: one row per invoice. Two
small changes would let it become the main source for payments instead of a cross-check:

- **Add the Project ID** to each invoice row, so an invoice belongs to a project without
  needing the invoice number to be retyped in the diary.
- **Split "Payment Status" into three columns:** status (Cleared / Not cleared / Part paid),
  amount received, and date received or due. Today that one column holds a status on some
  rows, a date on others and an amount on others.

The app found invoices in the INVOICE sheet that are not mentioned in any project's notes,
an invoice marked cleared there but "not cleared" in the master list, and an invoice amount
that differs from the project value. With a Project ID these become automatic checks.

### Project detail files

| Column | Why |
|---|---|
| **Unit price** / **Value** | Progress by value (change 5). |
| **ETA** as a real date with the year | "eta 15th Nov" cannot be compared with a due date. With real dates the app warns when an item is expected after the deadline. |
| **Line status** from a fixed list (Delivered, Partial, Pending, Out of stock, Re-ordered, Cancelled) | Today the Remarks column doubles as the status, with different spellings. |
| **Site / Lot** | For projects with several sites, houses or delivery lots, so progress can be shown per site. |
| **GI note** in its own column | Today goods-issue to-dos sit in a column without a header, mixed with shipment notes. |

Habits that prevent the problems the app flags:

- **Re-orders:** mark the *original* line "Re-ordered" and add the new order as a new row. The
  app currently detects re-orders by matching article and quantity, which is a good guess,
  not a certainty.
- **When goods arrive, update both the quantity and the status.** Several lines said "pending"
  while the delivered quantity equalled the ordered quantity. The app counts these as *not*
  delivered and lists them for checking.
- **One article number for one kind of item.** Where one number is used for different things
  (three sizes of the same product is fine; a fan and a valve is not), stock and re-order
  matching become unreliable.
- **Vendor on every open line.** A re-ordered line with no vendor cannot be chased.
- **Name the file with the customer code and project**, and keep one file per project.

---

## 3. Cleaning the old data: what is worth it

**Worth doing (minutes, through Corrections, no file editing):**

1. Download the Corrections file from the **Missing info** screen. It lists exactly the
   missing values, project by project. Filling in delivery periods and signing dates for the
   *open* projects gives the most.
2. Add a correction wherever the diary reads as "delivered" but something is still
   outstanding (for example a signed delivery note that is pending).
3. For projects marked partly paid with no clear balance, type the `unpaid` amount.

**Not worth doing:**

- Rewriting old diary text, fixing old typos, reformatting old dates.
- Completing projects that are delivered and paid. The app deliberately asks for nothing on
  those.
- Renumbering or re-sorting detail-file lines. The app keeps file order.

**A sensible routine:** once a week, open **Missing info** and **Needs attention** for the
late and at-risk projects only. Fix what you see there. The list shrinks quickly because the
same few fields are missing everywhere.

---

## 4. Entering and updating data

- **Append, don't overwrite.** Add a new dated line to the diary instead of rewriting the
  cell. The "what's new" feed works by comparing versions of the file.
- **Save a new version of the register on a rhythm** (for example every Monday) into the data
  folder under the same name. The Updates screen then shows the week's changes.
- **Use the drop-down lists** in the templates (Excel "Data validation"). They make
  "Delivered / delivered / DELIVERED-" impossible to mistype.
- **One shared folder.** If the files live on OneDrive, SharePoint or a network drive, point
  `data_folder` in `config.yaml` at that folder and the dashboard always reads the latest
  versions. Nobody needs to copy files around.
- **Close the file in Excel before refreshing** if the app says it is locked.

---

## 5. Editing inside the app later: three options

The dashboard is read-only on purpose. If you later want to type updates in the app:

| Option | How it works | Good | Less good |
|---|---|---|---|
| **A. Keep Excel as the source** (today) | You edit Excel; the app reads | Nothing new to learn; files stay yours; no lock-in | Updates depend on people saving files |
| **B. Small forms that write Corrections** | A form in the app adds a row to the Corrections file for you (set delivery status, due date, next action, add an update note) | You fix things where you see them; originals still untouched; a day or two of work | Two places hold information (Excel and Corrections) |
| **C. A small database as the source** | Projects, lines, invoices and updates live in a database (SQLite, free); Excel becomes import and export | One version of the truth; history of every change; several people at once | A real project: migration, backups, a person responsible |

**Recommendation:** stay with A while this is a personal proof of concept. Move to **B** as
soon as you find yourself opening Excel only to change a status. Consider **C** only when
several people need to update the same project at the same time, or when the Corrections file
grows past a few hundred rows. The code is already split so that step C replaces the
"reading" part only; the screens stay.

---

## 6. Other data worth adding, and what each unlocks

| Data | Where it could come from | What it would add |
|---|---|---|
| **Payments received** | Finance / SAP customer statement export | Real unpaid balances and ageing (30/60/90 days), instead of "partially cleared" |
| **Purchase orders and vendor ETAs** | SAP PO list export | Expected arrival per line, vendors that are repeatedly late, early warning before a project slips |
| **Stock levels for own-stock lines** | SAP stock report | Out-of-stock items known before the client asks |
| **Goods issue / delivery note status** | SAP delivery list | The goods-issue to-dos would be checked automatically rather than typed as notes |
| **Site or lot progress** | A "Site / Lot" column, or one sheet per site | Progress per pitch, house or lot for multi-site projects |
| **Performance guarantees and their expiry dates** | A column in the register | A warning before a guarantee expires |
| **Pipeline details** (expected value, chance, expected signing date) | Columns in the register | A simple forecast of upcoming work |
| **Client contacts and agreement references** | Columns in the register | One place to look when chasing |

Each of these is a new "source" in the code: one small reader file, with no change to the
rest. SAP exports are the most valuable because nobody has to type them.

---

## 7. If more people start using it

- **Same office, read-only:** run the app on one computer; others open the "phone" address
  shown at start-up in their browser.
- **Always on:** run it on a small office server or an always-on PC, with the data folder on
  the shared drive.
- **Outside the office or with logins:** this needs proper hosting and access control. Treat
  that as an IT project, because the files contain client names and amounts.
- **Keep real files out of public places.** The GitHub copy of this project contains only
  made-up sample data, and the `data` folder is excluded from it on purpose.

---

## 8. Known limits of the current version

- Delivery status read from diary text is a best guess. A typed Delivery status column or a
  Corrections row always wins.
- "Delivered because fully invoiced" is an assumption and is labelled as such. It can be
  switched off in `config.yaml`.
- Re-orders are detected by matching article number and quantity.
- Progress by quantity adds up different units (pieces, rolls, bags), so read it as a rough
  indication only.
- A detail file is linked by customer code when exactly one project carries that code. When
  one client has several projects, the app asks you to choose.
- Dates without a year ("13th June") are ignored.
- The app shows one currency and does not convert.
