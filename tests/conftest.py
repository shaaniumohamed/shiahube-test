"""Shared test set-up. All data is made up by tools/sample_data.py."""
import datetime as dt
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from projectdash import load_config, load_portfolio  # noqa: E402
from tools import sample_data  # noqa: E402

AS_OF = dt.date(2025, 11, 10)


@pytest.fixture(scope="session")
def cfg():
    return load_config(ROOT / "config.yaml")


@pytest.fixture(scope="session")
def sample_dir(tmp_path_factory):
    return sample_data.build_all(tmp_path_factory.mktemp("sample"))


@pytest.fixture(scope="session")
def pf(cfg, sample_dir):
    return load_portfolio(cfg, AS_OF, folder=str(sample_dir))


@pytest.fixture
def build(cfg, tmp_path):
    """Build a fresh sample folder with optional sheets and load it."""
    def _build(as_of=AS_OF, state=None, **kwargs):
        folder = sample_data.build_all(tmp_path / "data", **kwargs)
        return load_portfolio(cfg, as_of, state=state, folder=str(folder))
    return _build


def find(portfolio, text):
    """Same matching as the Corrections sheet: exact name first, else "contains"."""
    from projectdash.linking import find_projects
    hits = find_projects(portfolio.projects, text)
    assert len(hits) == 1, f"{text!r} matched {[p.name for p in hits]}"
    return hits[0]


def codes(project):
    return {f.code for f in project.flags}
