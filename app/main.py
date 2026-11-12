"""Project dashboard - start with:  streamlit run app/main.py   (or the start scripts)."""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
for folder in (str(ROOT), str(Path(__file__).resolve().parent)):
    if folder not in sys.path:
        sys.path.insert(0, folder)

from projectdash import load_config, load_portfolio  # noqa: E402
from projectdash.config import as_of_date  # noqa: E402
from projectdash.portfolio import choose_folder, folder_stamp  # noqa: E402
from projectdash.state import StateStore  # noqa: E402

import ui  # noqa: E402
from views import missing_info, payments, portfolio, project, to_deliver, updates  # noqa: E402

st.set_page_config(page_title="Project dashboard", page_icon=":material/monitoring:",
                   layout="wide", initial_sidebar_state="auto")
ui.css()


@st.cache_data(ttl=24 * 3600, show_spinner="Reading the Excel files…", max_entries=12)
def _load(folder: str, stamp: tuple, as_of: dt.date, cfg_json: str, links_stamp: float,
          today: dt.date):
    """Re-read only when a file, the settings, a saved link or the date changes."""
    cfg = json.loads(cfg_json)
    return load_portfolio(cfg, as_of, StateStore(cfg["state_folder"]), folder=folder, today=today)


# PROJECT_DASH_CONFIG lets a test or a second copy of the app use another settings file.
cfg = load_config(os.environ.get("PROJECT_DASH_CONFIG") or ROOT / "config.yaml")
state = StateStore(cfg["state_folder"])
folder, is_sample = choose_folder(cfg)
default_as_of = as_of_date(cfg, is_sample)
st.session_state["_asof_default"] = default_as_of

with st.sidebar:
    as_of = st.date_input(
        "Show the picture as of", value=default_as_of, key="asof", bind="query-params",
        format="DD/MM/YYYY",
        help="Lateness, 'due in N days' and 'last activity' are measured from this date. "
             "Change it to see how things stood on another day.")
    if as_of != dt.date.today():
        st.caption(f"Not today's date. Today is {dt.date.today():%d %b %Y}.")
    if st.button("Refresh files", icon=":material/refresh:", width="stretch",
                 help="Read the Excel files again now. The app also notices saved changes by itself."):
        st.cache_data.clear()
        st.rerun()

pf = _load(folder, folder_stamp(folder), as_of, json.dumps(cfg, default=str, sort_keys=True),
           state.stamp(), dt.date.today())
pf.is_sample = is_sample
st.session_state["_ctx"] = {"pf": pf, "cfg": cfg, "state": state, "as_of": as_of}

attention = sum(1 for p in pf.projects if p.status in ("Late", "At risk"))
open_lines = sum(1 for p in pf.projects for ln in p.lines if ln.open)
missing = sum(1 for p in pf.projects if p.missing) + len(pf.problems)
pages = [
    st.Page(portfolio.render, title="Portfolio", icon=":material/dashboard:", url_path="",
            default=True),
    st.Page(project.render, title="Project", icon=":material/assignment:", url_path="project"),
    st.Page(to_deliver.render, title=f"To deliver ({open_lines})" if open_lines else "To deliver",
            icon=":material/local_shipping:", url_path="to-deliver"),
    st.Page(updates.render, title="Updates", icon=":material/history:", url_path="updates"),
    st.Page(payments.render, title="Payments", icon=":material/payments:", url_path="payments"),
    st.Page(missing_info.render, title=f"Missing info ({missing})" if missing else "Missing info",
            icon=":material/rule:", url_path="missing-info"),
]
st.session_state["_pages"] = pages
with st.sidebar:
    st.caption(
        f"{len(pf.projects)} projects from {sum(1 for f in pf.files if f.kind != 'skipped')} "
        f"file(s) in `{Path(pf.folder).name}/`")
current = st.navigation(pages)
current.run()
