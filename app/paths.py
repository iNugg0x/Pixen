"""Cross-platform path helpers.

Centralizes the two things that differ between "running from source"
and "running as a frozen PyInstaller build", and between Windows /
Linux / macOS: where bundled assets live, and where per-user data
(autosaves, etc.) should be written. Everything else in the app should
go through here instead of constructing paths by hand.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QStandardPaths


def app_root() -> Path:
    """Directory that contains the app's own files.

    - Running from source (``python main.py``): the project root.
    - Frozen (PyInstaller onedir/onefile): the folder holding the
      executable, where ``datas`` from the .spec were copied
      (``sys._MEIPASS`` for onefile, the dist folder for onedir).
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent.parent


def asset_path(*parts: str) -> Path:
    """Resolve a path under ``assets/`` that works both from source and
    from a frozen build, e.g. ``asset_path("icons", "pixen.png")``."""
    return app_root() / "assets" / Path(*parts)


def user_data_dir() -> Path:
    """Per-user, writable app-data directory for this OS:

    - Windows: ``%LOCALAPPDATA%\\Pixen``
    - Linux:   ``$XDG_DATA_HOME/Pixen`` (usually ``~/.local/share/Pixen``)
    - macOS:   ``~/Library/Application Support/Pixen``

    Uses Qt's ``QStandardPaths`` so the actual location always matches
    OS convention instead of a hand-rolled guess. Requires
    ``QCoreApplication`` name/organization to already be set (done in
    ``main.py``) so Qt can build the right subfolder.
    """
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    if not base:
        base = str(Path.home() / ".pixen")
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path


def autosave_dir() -> Path:
    path = user_data_dir() / "autosave"
    path.mkdir(parents=True, exist_ok=True)
    return path
