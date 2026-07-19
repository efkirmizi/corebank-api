"""Executable enforcement of the dependency rule: api -> services -> repositories -> db.

If someone writes SQL in a route or imports Flask into a service, this fails in
CI instead of rotting into the architecture over time.
"""
from __future__ import annotations

import re
from pathlib import Path

APP = Path(__file__).resolve().parent.parent.parent / "app"


def _py_files(*subdirs: str) -> list[Path]:
    files: list[Path] = []
    for sub in subdirs:
        files.extend((APP / sub).rglob("*.py"))
    return files


def test_no_flask_import_in_services_or_repositories():
    offenders = []
    for path in _py_files("services", "repositories"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"^\s*(import flask|from flask)", text, re.MULTILINE):
            offenders.append(path.name)
    assert not offenders, f"Flask imported below the API layer: {offenders}"


def test_no_sql_execution_in_api_or_services():
    """SQL lives in repositories (and the db ping). The api and service layers
    must never touch a cursor directly."""
    offenders = []
    for path in _py_files("api", "services"):
        text = path.read_text(encoding="utf-8")
        if ".execute(" in text or ".cursor(" in text:
            offenders.append(path.name)
    assert not offenders, f"Direct SQL execution outside repositories: {offenders}"


def test_repositories_do_not_import_services_or_api():
    offenders = []
    for path in _py_files("repositories"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"from app\.(services|api)", text) or re.search(
            r"import app\.(services|api)", text
        ):
            offenders.append(path.name)
    assert not offenders, f"Repository imports an upper layer: {offenders}"


def test_services_do_not_import_api():
    offenders = []
    for path in _py_files("services"):
        text = path.read_text(encoding="utf-8")
        if re.search(r"from app\.api", text) or re.search(r"import app\.api", text):
            offenders.append(path.name)
    assert not offenders, f"Service imports the API layer: {offenders}"
