"""Settings from config.yaml, with a safe default for anything left out."""
from __future__ import annotations

import copy
import datetime as dt
from pathlib import Path
from typing import Any

import yaml

from .textnorm import to_date

DEFAULTS: dict[str, Any] = {
    "data_folder": "./data",
    "sample_folder": "./sample_data",
    "state_folder": "./.app_state",
    "as_of": "today",
    "sample_as_of": "2025-11-10",
    "currency": "MVR",
    "at_risk": {"due_within_days": 14, "progress_behind_points": 20},
    "stale_update_days": 30,
    "upcoming_days": 30,
    "date_typo_days": 30,
    "use_invoice_sheet": True,
    "assume_delivered_when_fully_invoiced": True,
    "fully_invoiced_percent": 99.5,
}


def _merge(base: dict, extra: dict) -> dict:
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _merge(base[key], value)
        elif value is not None:
            base[key] = value
    return base


def load_config(path: str | Path = "config.yaml") -> dict[str, Any]:
    """Read config.yaml. A missing or broken file falls back to the defaults."""
    path = Path(path)
    cfg = copy.deepcopy(DEFAULTS)
    cfg["config_problem"] = ""
    if path.is_file():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if isinstance(loaded, dict):
                _merge(cfg, loaded)
            else:
                cfg["config_problem"] = "config.yaml is not a list of settings; defaults are used."
        except yaml.YAMLError as exc:
            cfg["config_problem"] = f"config.yaml could not be read ({exc}); defaults are used."
    base = path.resolve().parent
    for key in ("data_folder", "sample_folder", "state_folder"):
        folder = Path(str(cfg[key])).expanduser()
        cfg[key] = str(folder if folder.is_absolute() else (base / folder))
    return cfg


def as_of_date(cfg: dict[str, Any], sample: bool = False) -> dt.date:
    """The date "today" is measured from: the config setting, else the real today."""
    value = cfg.get("sample_as_of") if sample else cfg.get("as_of")
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if value and str(value).strip().lower() != "today":
        parsed = to_date(str(value))
        if parsed:
            return parsed
    return dt.date.today()
