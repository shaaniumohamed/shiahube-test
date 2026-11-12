# Project delivery dashboard

A small dashboard that reads your existing Excel files **exactly as they are** and shows:

- which projects are late, at risk, on track or finished
- what is still to be delivered, line by line
- the latest updates from your notes, and what changed since the last file
- what is invoiced, unpaid or not yet sent
- a plain-English "Needs attention" list for every project

It never changes your Excel files. You do not need to clean up old data.

---

## 1. Install once

1. Install **Python** (version 3.11 or newer) from <https://www.python.org/downloads/>.
   - **Windows:** on the first screen of the installer, tick **"Add python.exe to PATH"**.
2. Download this folder to your computer (on GitHub: green **Code** button → **Download ZIP**, then unzip it).

That is all. The first start installs everything else by itself (it needs the internet for a few minutes).

## 2. Start the app

| Your computer | What to do |
|---|---|
| **Windows** | Double-click **`start.bat`** |
| **Mac** | Double-click **`start.command`** |

Use only the file for your kind of computer. On a Mac, ignore `start.bat`; on Windows, ignore
`start.command`. If a file opens as text in an editor, it is the one for the other kind of
computer.

**Mac, first time only.** macOS blocks files downloaded from the internet until you allow them:

1. Double-click `start.command`. If a message says it cannot be opened, click **Done**.
2. Open **System Settings → Privacy & Security** and scroll down to the message about
   `start.command`. Click **Open Anyway**, then confirm.
3. Double-click `start.command` again.

On older versions of macOS, right-click `start.command` → **Open** → **Open** does the same.

**Windows, first time only.** If a blue "Windows protected your PC" box appears, click
**More info** → **Run anyway**.

A window with text opens and, a moment later, the dashboard opens in your browser.
Keep the text window open while you use the dashboard. Close it to stop the app.

**On your phone:** the text window shows a second address ("On your phone"). Open it in the
phone's browser while the phone is on the same Wi-Fi as the computer.

## 3. Put your files in the `data` folder

Copy these into the **`data`** folder inside this folder:

- the **register** workbook (the master list with a "Project name" column)
- one **detail file** per project (the line items, with "Description" and "Quantity" columns)

File names do not matter, with one exception: if a detail file's name starts with the
customer code (for example `20004567 - Department of Public Works.xlsx`) and that code is in
the project name or client in the register, the app links the two by itself.

When you save a newer version of a file into the folder, the dashboard updates the next time
the page reloads, or press **Refresh files** on the left.

Until you add your own files, the app shows made-up sample projects so you can look around.

## 4. The screens

| Screen | What it is for |
|---|---|
| **Portfolio** | Every project, worst first. Search, filter by status, and switch between **List**, **Board** and **Table**. Click a project to open it. |
| **Project** | Status, delivery, due date, unpaid amount, the "Needs attention" list, every value with **where it came from**, the line items, and a timeline of your dated notes. |
| **To deliver** | Every line that is still open, across all projects. Group by project, vendor or status. |
| **Updates** | New notes since the previous version of the register, the latest dated entries, and projects with no recent update. |
| **Payments** | Invoiced, received, unpaid and "invoiced but not sent". |
| **Missing info** | The few values that would make the dashboard more useful, with a ready-made Excel file to fill in. Also lists every file and what the app took from it. |

**"Show the picture as of"** (left side) changes the date lateness is measured from. It is
today by default.

### What the statuses mean

| Status | Meaning |
|---|---|
| Late | The due date has passed and delivery is not complete. |
| At risk | Due within 14 days, or delivery is well behind the time used, or an item's ETA is after the due date. |
| On track | Has a due date and nothing suggests it will be missed. |
| No deadline | In hand, but no due date can be worked out (usually no delivery period is recorded). |
| Unclear | The notes don't say whether anything was delivered, and there is no due date. |
| Complete | Delivered. |
| Pipeline | Not signed or started yet. |

The due date is the agreement signing date plus the agreed delivery period, unless you give
a due date yourself.

## 5. Fixing a value: the Corrections sheet

When the app reads something wrong, or a value is missing, you fix it in **one place** without
touching the original cell.

**Easiest way:** open **Missing info** → **Download Corrections file** → type the values →
save the file into the `data` folder → **Refresh files**.

**By hand:** add a sheet named **`Corrections`** to the register workbook (or keep it in a
separate workbook in the `data` folder) with these four headers:

| project | field | value | note |
|---|---|---|---|
| Lagoon City water meters | delivery_days | 90 | from the signed agreement |
| Phase-II | delivery_status | Partly delivered | signed delivery note pending |

- **project**: the project name, or any part of it that only one project contains.
- **field**: one of the names below.
- **value**: the correct value.
- **note**: optional; it is shown next to the value in the app.

| field | what to type |
|---|---|
| `contract_value` | a number, e.g. 1250000.50 |
| `request_date` | a date, e.g. 18.12.2023 |
| `agreement_date` | the date the agreement was signed |
| `delivery_days` | the delivery period in days, e.g. 45 |
| `due_date` | a date (only if it is not signing date + days) |
| `delivery_status` | Not started, In progress, Partly delivered or Delivered |
| `payment_status` | Unpaid, Partly paid, Invoice not sent, Not invoiced or Paid |
| `unpaid` | the amount still owed |
| `next_action` | a few words |

Corrected values are labelled **correction** in the app. If a row cannot be used (for example
the project text matches two projects), the app tells you on the **Missing info** screen.

## 6. Linking a detail file to a project: the Links sheet

The app links a detail file by itself when it finds the customer code or a shared Sales Order
number. When it cannot, the **Portfolio** screen shows the file with a drop-down list: pick
the project once and the app remembers.

If you prefer to keep it in Excel, add a sheet named **`Links`**:

| file | project |
|---|---|
| water meters | Water meters for Lagoon City |

## 7. Settings

Open **`config.yaml`** with Notepad (Windows) or TextEdit (Mac). Each setting has a line of
explanation above it: the data folder, the "at risk" thresholds, how many days without a dated
note counts as "no recent update", and so on. Save the file and press **Refresh files**.

## 8. Templates and suggestions

- **`templates/`** has three ready-to-use Excel files: a Corrections and Links file, a project
  detail file and a register, with drop-down lists. The blue headers are optional new columns.
- **`docs/SUGGESTIONS.md`** explains, in plain language, how to make the data easier going
  forward without redoing the old files.

## If something goes wrong

| What you see | What to do |
|---|---|
| "Python is not installed" | Install Python (step 1) and start again. On Windows, tick "Add python.exe to PATH". |
| The start file opens as text in an editor | You opened the file for the other kind of computer. On a Mac use `start.command`; on Windows use `start.bat`. |
| Mac: "cannot be opened" or "not verified" | See "Mac, first time only" above. Or open the **Terminal** app, type `cd ` (with a space), drag the project folder into the window, press Enter, then type `bash start.command` and press Enter. |
| "Set-up failed" | Check the internet connection and start again. |
| A file is listed as "not read: the file is locked" | Close it in Excel and press **Refresh files**. |
| A file is listed as "skipped" | The app found no "Project name" header and no "Description" + "Quantity" headers in it. |
| Old `.xls` file | Open it in Excel and use **Save As → Excel Workbook (.xlsx)**. |
| A value looks wrong | Open the project, look at **What the app read** to see where the value came from, then add a Corrections row. |

---

## For a developer

```
projectdash/        reading and rules (no web code, unit-tested)
  sources/          one reader per kind of file; add a module here for a new kind of data
  notes.py          rules for the free-text diaries        lines.py   rules for line items
  resolve.py        the override layers                    status.py  Late / At risk / …
  attention.py      "Needs attention" items                portfolio.py  load_portfolio(): the one entry point
app/                Streamlit screens (only presentation)
tools/              builds the made-up sample data and the templates
tests/              pytest suite on made-up data
```

```bash
pip install -r requirements-dev.txt
```

```bash
python -m pytest
```

```bash
python -m streamlit run app/main.py
```

All sample data in this repository is invented. Real project files belong in `data/`, which
git ignores.
