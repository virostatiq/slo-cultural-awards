"""The decision scripts must be no-ops on the committed data.

A script that changes data/ on a re-run means a decision fires twice (as when a
drop written for pre-shift ids deleted a shifted Zlata ptica edition). The log
dedupes repeated rows, so "0 changes applied" alone does not prove this.
"""

import importlib.util
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ["apply_edition_decisions", "apply_name_decisions", "add_awards"]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("name", SCRIPTS)
def test_script_is_idempotent(name, tmp_path, monkeypatch):
    data = tmp_path / "data"
    shutil.copytree(ROOT / "data", data)
    mod = load(name)
    monkeypatch.setattr(mod, "DATA", data)
    monkeypatch.setattr(mod, "LOG", data / "meta" / mod.LOG.name)
    if hasattr(mod, "ROOT"):
        monkeypatch.setattr(mod, "ROOT", tmp_path)
        shutil.copytree(ROOT / "docs", tmp_path / "docs")
        if hasattr(mod, "REVIEW"):
            monkeypatch.setattr(mod, "REVIEW", tmp_path / mod.REVIEW.relative_to(ROOT))
    mod.main()
    changed = [p.name for p in sorted((ROOT / "data").rglob("*.csv"))
               if p.read_bytes() != (data / p.relative_to(ROOT / "data")).read_bytes()]
    assert not changed, f"{name} changed {changed} on a re-run"
