from __future__ import annotations

import tomllib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_operator_ui_smoke_script_is_committed_and_exercises_core_workflows():
    script = ROOT / "scripts" / "operator_ui_smoke.py"

    text = script.read_text(encoding="utf-8")

    assert "sync_playwright" in text
    assert "AUTO_CRYPTO_BROWSER_PATH" in text
    assert "global halt" in text
    assert "portfolio bracket trigger exit" in text
    assert "load bitunix tickers" in text
    assert "export audit csv" in text


def test_operator_ui_smoke_script_has_dev_dependency_and_readme_command():
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = pyproject["project"]["optional-dependencies"]["dev"]

    assert any(dependency.startswith("playwright") for dependency in dev_dependencies)

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "scripts/operator_ui_smoke.py" in readme
    assert "AUTO_CRYPTO_BROWSER_PATH" in readme
