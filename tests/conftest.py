"""Shared pytest fixtures.

A single QApplication is required before touching most Qt classes
(QImage/QPainter included, in current Qt6). Tests run headless via the
"offscreen" platform plugin -- set as the default here so `pytest` works
locally without a display, and CI doesn't need to configure it per-OS.
CI additionally sets QT_QPA_PLATFORM=offscreen as a belt-and-suspenders
measure; either is sufficient on its own.
"""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    app.setOrganizationName("Pixen")
    app.setApplicationName("Pixen")
    yield app
