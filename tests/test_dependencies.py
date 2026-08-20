"""Confirms requirements.txt isn't lying: everything listed there is
importable, and PySide6 exposes the Qt submodules Pixen actually uses
(QtWidgets, QtGui, QtCore, QtPrintSupport)."""
import importlib

import PySide6
import numpy


def test_pyside6_importable():
    assert PySide6.__version__


def test_numpy_importable():
    assert numpy.__version__


def test_required_qt_submodules_importable():
    for mod in ("PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "PySide6.QtPrintSupport"):
        importlib.import_module(mod)


def test_requirements_txt_matches_pyproject():
    """Both dependency lists exist purely so this can't silently drift:
    pyproject.toml is authoritative (used for `pip install -e .` and
    packaging metadata), requirements.txt is the quick `pip install -r`
    path the README documents -- they should always name the same
    packages."""
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    req_lines = [l.strip() for l in (root / "requirements.txt").read_text().splitlines() if l.strip()]
    req_names = {re.split(r"[><=]", l)[0].strip().lower() for l in req_lines}

    pyproject_text = (root / "pyproject.toml").read_text()
    deps_block = re.search(r"dependencies\s*=\s*\[(.*?)\]", pyproject_text, re.S).group(1)
    pyproject_names = {
        re.split(r"[><=]", dep.strip().strip('",'))[0].strip().lower()
        for dep in deps_block.splitlines() if dep.strip().strip('",')
    }

    assert req_names == pyproject_names
