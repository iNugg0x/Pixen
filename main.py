"""Pixen -- entry point.

Run with:  python main.py
"""
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow

ICON_PATH = Path(__file__).resolve().parent / "assets" / "icons" / "pixen.png"


def main():
    # HiDPI is on by default in Qt6, but this keeps behaviour explicit
    # and consistent across Windows scaling settings.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Pixen")
    app.setApplicationDisplayName("Pixen")
    app.setOrganizationName("Pixen")
    if ICON_PATH.exists():
        app.setWindowIcon(QIcon(str(ICON_PATH)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
