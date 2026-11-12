"""Small things the app remembers on this computer, kept as readable JSON files.

Only two things are stored: which project you picked for a detail file that
could not be linked automatically, and a snapshot of the previous version of
each file so the app can show what changed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StateStore:
    def __init__(self, folder: str | Path):
        self.folder = Path(folder)

    def _path(self, name: str) -> Path:
        return self.folder / f"{name}.json"

    def load(self, name: str) -> dict[str, Any]:
        try:
            data = json.loads(self._path(name).read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    def save(self, name: str, data: dict[str, Any]) -> None:
        try:
            self.folder.mkdir(parents=True, exist_ok=True)
            tmp = self._path(name).with_suffix(".tmp")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.replace(self._path(name))
        except OSError:
            pass                      # remembering is a convenience, never a reason to fail

    # ---- chosen links: detail file name -> project name
    def links(self) -> dict[str, str]:
        return {k: v for k, v in self.load("links").items() if isinstance(v, str)}

    def save_link(self, file_name: str, project_name: str) -> None:
        data = self.load("links")
        data[file_name] = project_name
        self.save("links", data)

    def remove_link(self, file_name: str) -> None:
        data = self.load("links")
        if data.pop(file_name, None) is not None:
            self.save("links", data)

    def stamp(self) -> float:
        """Changes whenever a saved link changes (used to refresh the cache)."""
        try:
            return self._path("links").stat().st_mtime
        except OSError:
            return 0.0
