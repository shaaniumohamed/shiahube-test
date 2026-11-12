"""Shared look and small building blocks for every screen.

Only presentation lives here. All reading and calculating is in ``projectdash``.
"""
from __future__ import annotations

import datetime as dt
import html
from urllib.parse import urlencode

import streamlit as st

from projectdash import model as M

# Status colours follow a fixed "state" palette; every chip also carries its label.
STATUS_COLOR = {
    M.S_LATE: "#d03b3b",
    M.S_AT_RISK: "#fab219",
    M.S_UNCLEAR: "#898781",
    M.S_NO_DEADLINE: "#c3c2b7",
    M.S_ON_TRACK: "#0ca30c",
    M.S_COMPLETE: "#2a78d6",
    M.S_PIPELINE: "#e1e0d9",
}
STATUS_HELP = {
    M.S_LATE: "Past the due date and not fully delivered",
    M.S_AT_RISK: "Due soon, behind schedule, or an item is expected after the due date",
    M.S_UNCLEAR: "Delivery status is not known and there is no due date",
    M.S_NO_DEADLINE: "In hand, but no due date can be worked out",
    M.S_ON_TRACK: "Has a due date and nothing suggests it will be missed",
    M.S_COMPLETE: "Delivered",
    M.S_PIPELINE: "Not signed or started yet",
}
LINE_COLOR = {
    M.L_DELIVERED: "#0ca30c", M.L_PARTIAL: "#fab219", M.L_PENDING: "#ec835a",
    M.L_OUT_OF_STOCK: "#d03b3b", M.L_REORDERED: "#c3c2b7", M.L_CANCELLED: "#c3c2b7",
}
SOURCE_HELP = {
    M.SRC_CORRECTION: "From your Corrections sheet",
    M.SRC_COLUMN: "From a column in the master list",
    M.SRC_DETAIL: "From the linked detail file",
    M.SRC_NOTES: "Read from the free-text notes",
    M.SRC_CALC: "Worked out by the app",
    M.SRC_ASSUMED: "Assumed because the full value is invoiced",
    M.SRC_INVOICE_SHEET: "From the INVOICE sheet",
    M.SRC_NONE: "Not found in the files",
}

CSS = """
<style>
:root {
  --plane:#f9f9f7; --card:#ffffff; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
  --hair:#e1e0d9; --axis:#c3c2b7; --accent:#2a78d6; --track:#cde2fb;
  --critical:#d03b3b; --warning:#fab219; --good:#0ca30c; --serious:#ec835a;
}
.block-container { padding-top: 2.6rem; padding-bottom: 4rem; max-width: 1320px; }
.pd, .pd * { box-sizing: border-box; }
.pd { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; color: var(--ink); }
.pd a { color: inherit; text-decoration: none; }
.pd .muted { color: var(--muted); } .pd .ink2 { color: var(--ink2); }
.pd .num { font-variant-numeric: tabular-nums; }

/* page heading */
.pd-head h1 { font-size: 1.55rem; font-weight: 650; margin: 0 0 .15rem; letter-spacing: -.01em; }
.pd-head p { margin: 0; color: var(--ink2); font-size: .9rem; }
.pd-head .crumb { font-size: .85rem; color: var(--accent); display: inline-block; margin-bottom: .5rem; }
.pd-head .crumb:hover { text-decoration: underline; }
.pd h2 { font-size: 1.02rem; font-weight: 650; margin: 1.6rem 0 .6rem; }
.pd h2 small { font-weight: 400; color: var(--muted); font-size: .82rem; margin-left: .4rem; }

/* stat tiles */
.tiles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 1rem 0 .4rem; }
.tile { background: var(--card); border: 1px solid var(--hair); border-radius: 12px; padding: 14px 16px; min-width: 0; }
.tile .label { font-size: .8rem; color: var(--ink2); }
.tile .value { font-size: 1.7rem; font-weight: 650; line-height: 1.25; letter-spacing: -.01em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.tile .value small { font-size: .85rem; font-weight: 500; color: var(--muted); margin-left: .25rem; }
.tile .sub { font-size: .8rem; color: var(--muted); margin-top: 2px; }
.tile.alert { border-left: 4px solid var(--critical); }
.tile.warn { border-left: 4px solid var(--warning); }

/* chips */
.chip { display: inline-flex; align-items: center; gap: 6px; padding: 2px 9px 2px 8px; border-radius: 999px;
        font-size: .78rem; font-weight: 550; background: #f3f2ee; color: var(--ink); white-space: nowrap; line-height: 1.5; }
.chip i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; flex: none; }
.chip.ghost { background: transparent; border: 1px solid var(--hair); color: var(--ink2); font-weight: 450; }
.src { font-size: .72rem; color: var(--ink2); border: 1px solid var(--hair); border-radius: 6px; padding: 1px 6px; white-space: nowrap; background: #fbfbfa; }
.src.correction { border-color: var(--accent); color: #1c5cab; background: #eef5fe; }
.src.none { color: var(--muted); border-style: dashed; }
.count { display: inline-flex; min-width: 24px; height: 24px; align-items: center; justify-content: center; border-radius: 999px;
         font-size: .78rem; font-weight: 650; background: #fdf0d2; color: var(--ink); padding: 0 7px; }
.count.urgent { background: #f9dcdc; } .count.zero { background: transparent; color: var(--axis); font-weight: 400; }
.tag { font-size: .72rem; color: var(--ink2); background: #eef5fe; border-radius: 5px; padding: 1px 6px; white-space: nowrap; }
.tag.new { background: #dff5df; }

/* delivery meter */
.meter { height: 8px; border-radius: 999px; background: var(--track); overflow: hidden; min-width: 60px; }
.meter b { display: block; height: 100%; border-radius: 999px; background: var(--accent); }
.meter.late { background: #f6d5d5; } .meter.late b { background: var(--critical); }
.meter.done { background: #cfeccf; } .meter.done b { background: var(--good); }

/* status share bar */
.share { display: flex; gap: 2px; height: 8px; margin: .9rem 0 .45rem; }
.share span { display: block; height: 100%; border-radius: 999px; min-width: 6px; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 16px; font-size: .8rem; color: var(--ink2); }
.legend span { display: inline-flex; align-items: center; gap: 6px; }
.legend i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.legend b { color: var(--ink); font-weight: 600; }

/* project list */
.plist { border: 1px solid var(--hair); border-radius: 12px; background: var(--card); overflow: hidden; }
.plist .hd, .plist a.row { display: grid; grid-template-columns: minmax(0, 3.2fr) 92px minmax(120px, 1.3fr) 118px minmax(118px, 1fr) 44px; gap: 14px; align-items: center; padding: 11px 16px; }
.plist .hd { font-size: .72rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); border-bottom: 1px solid var(--hair); background: #fbfbfa; padding-top: 8px; padding-bottom: 8px; }
.plist a.row { border-bottom: 1px solid var(--hair); transition: background .12s; }
.plist a.row:last-child { border-bottom: 0; }
.plist a.row:hover { background: #f5f8fd; }
.plist .name { font-weight: 600; font-size: .93rem; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.plist .meta { font-size: .8rem; color: var(--ink2); display: flex; flex-wrap: wrap; gap: 3px 8px; align-items: center; margin-top: 2px; }
.plist .val { text-align: right; font-size: .9rem; }
.plist .small { font-size: .78rem; color: var(--ink2); margin-top: 3px; }
.plist .due b { font-weight: 600; font-size: .88rem; }
.plist .r { text-align: right; }
.empty { border: 1px dashed var(--axis); border-radius: 12px; padding: 22px; color: var(--ink2); text-align: center; font-size: .9rem; }

/* board */
.board { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(220px, 1fr); gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.board .col { background: #f3f2ee; border-radius: 12px; padding: 10px; min-height: 80px; }
.board .col h3 { font-size: .8rem; margin: 2px 4px 8px; font-weight: 650; display: flex; align-items: center; gap: 6px; }
.board .col h3 i { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.board .col h3 span { color: var(--muted); font-weight: 400; }
.board a.card { display: block; background: var(--card); border: 1px solid var(--hair); border-radius: 10px; padding: 9px 11px; margin-bottom: 8px; }
.board a.card:hover { border-color: var(--accent); }
.board .card .name { font-size: .84rem; font-weight: 600; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.board .card .meta { font-size: .76rem; color: var(--ink2); margin-top: 3px; display: flex; justify-content: space-between; gap: 8px; }
.board .card .meter { margin-top: 7px; }

/* coming up */
.upnext { display: flex; flex-wrap: wrap; gap: 8px; }
.upnext a { border: 1px solid var(--hair); background: var(--card); border-radius: 10px; padding: 7px 12px; font-size: .84rem; display: inline-flex; gap: 8px; align-items: baseline; }
.upnext a:hover { border-color: var(--accent); }
.upnext a b { font-weight: 600; } .upnext a span { color: var(--ink2); font-size: .8rem; }

/* generic tables */
.tbl { width: 100%; border-collapse: collapse; font-size: .86rem; background: var(--card); }
.tblwrap { border: 1px solid var(--hair); border-radius: 12px; overflow-x: auto; background: var(--card); }
.tbl th { text-align: left; font-size: .72rem; text-transform: uppercase; letter-spacing: .04em; color: var(--muted); font-weight: 500; padding: 8px 12px; border-bottom: 1px solid var(--hair); background: #fbfbfa; white-space: nowrap; }
.tbl td { padding: 8px 12px; border-bottom: 1px solid var(--hair); vertical-align: top; }
.tbl tr:last-child td { border-bottom: 0; }
.tbl td.r, .tbl th.r { text-align: right; }
.tbl td.nw { white-space: nowrap; }
.tbl .sub { font-size: .78rem; color: var(--ink2); margin-top: 2px; }
.tbl tr.dim td { color: var(--muted); }
.tbl .wide { min-width: 240px; }
.tbl a.lnk { color: #1c5cab; } .tbl a.lnk:hover { text-decoration: underline; }

/* needs attention */
.flags { display: grid; gap: 6px; }
.flag { display: flex; gap: 10px; align-items: flex-start; background: var(--card); border: 1px solid var(--hair); border-left: 4px solid var(--warning); border-radius: 8px; padding: 8px 12px; font-size: .88rem; }
.flag.urgent { border-left-color: var(--critical); }
.flag.info { border-left-color: var(--axis); color: var(--ink2); }
.flag .ic { flex: none; font-weight: 700; width: 16px; text-align: center; color: var(--ink2); }

/* timeline */
.tl { border-left: 2px solid var(--hair); margin-left: 6px; padding-left: 16px; display: grid; gap: 10px; }
.tl .e { position: relative; font-size: .88rem; }
.tl .e::before { content: ""; position: absolute; left: -22px; top: 6px; width: 10px; height: 10px; border-radius: 50%; background: var(--card); border: 2px solid var(--axis); }
.tl .e.new::before { border-color: var(--good); background: #dff5df; }
.tl .d { font-weight: 600; margin-right: 8px; white-space: nowrap; }
.tl .w { color: var(--muted); font-size: .76rem; margin-left: 6px; }
.orig { white-space: pre-wrap; background: #fbfbfa; border: 1px solid var(--hair); border-radius: 8px; padding: 10px 12px; font-size: .84rem; margin: 0 0 10px; font-family: inherit; }
.orig-label { font-size: .76rem; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; margin-bottom: 3px; }

.banner { border: 1px solid var(--hair); border-left: 4px solid var(--accent); background: #f5f8fd; border-radius: 8px; padding: 9px 13px; font-size: .88rem; margin: .5rem 0; }
.banner.warn { border-left-color: var(--warning); background: #fffaf0; }

@media (max-width: 760px) {
  .block-container { padding: 3.6rem 1rem 3rem; }
  .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .tile .value { font-size: 1.35rem; }
  .plist .hd { display: none; }
  .plist a.row { grid-template-columns: minmax(0, 1fr) auto; gap: 6px 10px; align-items: center; }
  .plist a.row > .c-name { grid-column: 1 / -1; order: 1; }
  .plist a.row > .c-st { order: 2; }
  .plist a.row > .c-due { order: 3; text-align: right; }
  .plist a.row > .c-del { order: 4; }
  .plist a.row > .c-val { order: 5; text-align: right; }
  .plist a.row > .c-fl { display: none; }
  .plist .due .small { display: inline; margin-left: 6px; }
  .plist .name { -webkit-line-clamp: 3; }
  .board { grid-auto-columns: 78%; }
  .tbl { font-size: .82rem; } .tbl td, .tbl th { padding: 7px 9px; }
}
</style>
"""


def esc(value) -> str:
    return html.escape("" if value is None else str(value))


def css() -> None:
    st.html(CSS)


def money(value: float | None, compact: bool = False) -> str:
    if value is None:
        return "—"
    if compact:
        a = abs(value)
        if a >= 1e9:
            return f"{value / 1e9:.2f}B"
        if a >= 1e6:
            return f"{value / 1e6:.2f}M"
        if a >= 1e4:
            return f"{value / 1e3:.0f}K"
        return f"{value:,.0f}"
    return f"{value:,.2f}"


def day(value: dt.date | None, short: bool = False) -> str:
    if value is None:
        return "—"
    return value.strftime("%d %b %Y") if not short else value.strftime("%d %b %y")


def qty(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


def ago(date: dt.date | None, as_of: dt.date) -> str:
    if date is None:
        return "no dated notes"
    days = (as_of - date).days
    if days < 0:
        return f"in {-days} days"
    if days == 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 60:
        return f"{days} days ago"
    if days < 730:
        return f"{days // 30} months ago"
    return f"{days // 365} years ago"


def chip(status: str, colors: dict | None = None) -> str:
    color = (colors or STATUS_COLOR).get(status, "#c3c2b7")
    tip = STATUS_HELP.get(status, "")
    return f'<span class="chip" title="{esc(tip)}"><i style="background:{color}"></i>{esc(status)}</span>'


def line_chip(status: str) -> str:
    return chip(status, LINE_COLOR)


def source(label: str) -> str:
    cls = "correction" if label == M.SRC_CORRECTION else "none" if label == M.SRC_NONE else ""
    return f'<span class="src {cls}" title="{esc(SOURCE_HELP.get(label, ""))}">{esc(label)}</span>'


def meter(percent: float | None, kind: str = "") -> str:
    pct = max(0.0, min(100.0, percent or 0.0))
    return f'<div class="meter {kind}"><b style="width:{pct:.0f}%"></b></div>'


def href(page: str = "", **params) -> str:
    """Link to a page that keeps the chosen "as of" date."""
    as_of = st.session_state.get("asof")
    default = st.session_state.get("_asof_default")
    query = {k: v for k, v in params.items() if v not in (None, "")}
    if isinstance(as_of, dt.date) and as_of != default:
        query["asof"] = as_of.isoformat()
    return f"{page or './'}{'?' + urlencode(query, doseq=True) if query else ''}"


def project_href(project: M.Project) -> str:
    return href("project", p=project.key)


def head(title: str, subtitle: str = "", crumb: tuple[str, str] | None = None) -> None:
    back = f'<a class="crumb" href="{esc(crumb[1])}" target="_self">← {esc(crumb[0])}</a><br>' if crumb else ""
    st.html(f'<div class="pd pd-head">{back}<h1>{esc(title)}</h1>'
            f'{f"<p>{subtitle}</p>" if subtitle else ""}</div>')


def h2(title: str, small: str = "") -> None:
    st.html(f'<div class="pd"><h2>{esc(title)}{f"<small>{esc(small)}</small>" if small else ""}</h2></div>')


def tiles(items: list[dict]) -> None:
    """Stat tiles. Each item: label, value, optional unit, sub, tone ("alert"/"warn")."""
    parts = []
    for it in items:
        unit = f'<small>{esc(it["unit"])}</small>' if it.get("unit") else ""
        parts.append(
            f'<div class="tile {it.get("tone", "")}"><div class="label">{esc(it["label"])}</div>'
            f'<div class="value" title="{esc(it.get("title", ""))}">{esc(it["value"])}{unit}</div>'
            f'<div class="sub">{esc(it.get("sub", ""))}&nbsp;</div></div>')
    st.html(f'<div class="pd tiles">{"".join(parts)}</div>')


def table(headers: list, rows: list[list[str]], right: set[int] | None = None,
          row_classes: list[str] | None = None) -> None:
    """A plain HTML table. Cells are already-escaped HTML strings."""
    right = right or set()
    th = "".join(f'<th class="{"r" if i in right else ""}">{esc(h)}</th>' for i, h in enumerate(headers))
    body = []
    for n, row in enumerate(rows):
        cls = row_classes[n] if row_classes else ""
        tds = "".join(f'<td class="{"r num" if i in right else ""}">{c}</td>' for i, c in enumerate(row))
        body.append(f'<tr class="{cls}">{tds}</tr>')
    st.html(f'<div class="pd tblwrap"><table class="tbl"><thead><tr>{th}</tr></thead>'
            f'<tbody>{"".join(body)}</tbody></table></div>')


def flags(items: list[M.Flag]) -> None:
    if not items:
        st.html('<div class="pd empty">Nothing needs attention.</div>')
        return
    icon = {"urgent": "!", "attention": "•", "info": "i"}
    rows = "".join(f'<div class="flag {esc(f.level)}"><span class="ic">{icon.get(f.level, "•")}</span>'
                   f'<span>{esc(f.text)}</span></div>' for f in items)
    st.html(f'<div class="pd flags">{rows}</div>')


def banner(text_html: str, warn: bool = False) -> None:
    st.html(f'<div class="pd banner {"warn" if warn else ""}">{text_html}</div>')


def empty(text: str) -> None:
    st.html(f'<div class="pd empty">{esc(text)}</div>')


def ctx():
    """The portfolio and settings prepared by main.py for this run."""
    return st.session_state["_ctx"]
