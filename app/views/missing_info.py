"""Missing info: what to fill in, reading problems, and what each file was used for."""
from __future__ import annotations

import streamlit as st

import ui
from projectdash import model as M
from projectdash.export import corrections_workbook
from projectdash.resolve import FIELD_HELP

FIELD_LABEL = {
    "contract_value": "Contract value", "request_date": "Request date",
    "agreement_date": "Agreement signing date", "delivery_days": "Delivery period (days)",
    "due_date": "Due date", "delivery_status": "Delivery status",
    "payment_status": "Payment status", "unpaid": "Unpaid amount", "next_action": "Next action",
}


def render() -> None:
    c = ui.ctx()
    pf = c["pf"]
    ui.head("Missing info", "The few values that would make the dashboard more useful. "
                            "Nothing here requires changing your existing files.")
    todo = [p for p in pf.projects if p.missing]
    no_deadline = [p for p in pf.projects if p.status in (M.S_NO_DEADLINE, M.S_UNCLEAR)]
    ui.tiles([
        {"label": "Projects with something missing", "value": len(todo),
         "sub": f"{sum(len(p.missing) for p in todo)} values in total"},
        {"label": "Cannot be checked for lateness", "value": len(no_deadline),
         "sub": "no due date can be worked out", "tone": "warn" if no_deadline else ""},
        {"label": "Reading problems", "value": len(pf.problems),
         "sub": "rows or files the app could not use", "tone": "warn" if pf.problems else ""},
        {"label": "Detail files not linked", "value": len(pf.unlinked),
         "sub": "choose their project on the Portfolio page" if pf.unlinked else "all linked"},
    ])

    ui.h2("What to fill in", "open projects only; finished and pipeline projects are left alone")
    if not todo:
        ui.empty("Nothing is missing for the open projects.")
    else:
        rows = []
        for p in todo:
            wanted = "".join(f'<div>{ui.esc(FIELD_LABEL.get(f, f))}'
                             f'<span class="sub" style="display:inline;margin-left:8px">'
                             f'{ui.esc(FIELD_HELP.get(f, ""))}</span></div>' for f in p.missing)
            rows.append([f'<a class="lnk" href="{ui.esc(ui.project_href(p))}" target="_self">'
                         f'{ui.esc(p.name[:80])}</a><div class="sub">{ui.esc(p.client)}</div>',
                         ui.chip(p.status), wanted])
        ui.table(["Project", "Status", "Missing"], rows)
        st.markdown(
            "**The quick way to fill these in:** download the file below, type the values in the "
            "`value` column, save it into your data folder and press *Refresh files*. "
            "Rows you leave empty are ignored. Your original files are not touched.")
        st.download_button("Download Corrections file (Excel)", corrections_workbook(pf),
                           file_name="Corrections.xlsx", icon=":material/download:", type="primary",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    ui.h2("Reading problems", f"{len(pf.problems)}")
    if pf.problems:
        ui.flags([M.Flag("problem", text) for text in pf.problems])
    else:
        ui.empty("Every file and every Corrections / Links row was understood.")

    ui.h2("Files in the data folder", pf.folder)
    kind_color = {"register": "#2a78d6", "detail file": "#0ca30c", "corrections": "#6250d6",
                  "invoice sheet": "#2a78d6", "skipped": "#c3c2b7", "problem": "#d03b3b"}
    linked = {d.name: p for p in pf.projects for d in p.detail_files}
    rows = []
    for f in pf.files:
        used = ui.esc(f.detail)
        if f.name in linked:
            p = linked[f.name]
            used += (f'<div class="sub">linked to <a class="lnk" href="{ui.esc(ui.project_href(p))}" '
                     f'target="_self">{ui.esc(p.name[:70])}</a></div>')
        elif f.kind == "detail file":
            used += '<div class="sub"><b>not linked to a project yet</b></div>'
        rows.append([ui.esc(f.name), ui.chip(f.kind, kind_color), used])
    if rows:
        ui.table(["File", "Read as", "What the app took from it"], rows)
    else:
        ui.empty("The data folder has no Excel files.")
