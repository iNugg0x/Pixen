from __future__ import annotations

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                                QPushButton, QColorDialog, QLabel, QToolButton)


DEFAULT_PALETTE = [
    "#000000", "#404040", "#7f7f7f", "#bfbfbf", "#ffffff",
    "#a51c30", "#ff3b30", "#ff9500", "#ffcc00", "#34c759",
    "#00b894", "#00c7be", "#32ade6", "#007aff", "#5856d6",
    "#af52de", "#ff2d92", "#8b572a", "#6e6e6e", "#c69c6d",
]


class ColorSwatch(QWidget):
    clicked = Signal()
    rightClicked = Signal()

    def __init__(self, color: QColor, size: int = 22, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.setBrush(self.color)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 3, 3)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.RightButton:
            self.rightClicked.emit()


class PrimarySecondaryIndicator(QWidget):
    """Overlapping primary/secondary color squares, Paint-classic style."""
    swapRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.primary = QColor(Qt.black)
        self.secondary = QColor(Qt.white)
        self.setFixedSize(40, 40)
        self.setCursor(Qt.PointingHandCursor)

    def set_colors(self, primary: QColor, secondary: QColor):
        self.primary, self.secondary = QColor(primary), QColor(secondary)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.setBrush(self.secondary)
        painter.drawRect(16, 16, 20, 20)
        painter.setBrush(self.primary)
        painter.drawRect(2, 2, 20, 20)

    def mousePressEvent(self, event):
        self.swapRequested.emit()


class ColorPanel(QWidget):
    primaryChanged = Signal(QColor)
    secondaryChanged = Signal(QColor)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.primary_color = QColor(Qt.black)
        self.secondary_color = QColor(Qt.white)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6)

        self.indicator = PrimarySecondaryIndicator()
        self.indicator.swapRequested.connect(self.swap_colors)
        layout.addWidget(self.indicator)

        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(2)
        grid.setContentsMargins(0, 0, 0, 0)
        for i, hexcolor in enumerate(DEFAULT_PALETTE):
            swatch = ColorSwatch(QColor(hexcolor))
            swatch.clicked.connect(lambda c=hexcolor: self.set_primary(QColor(c)))
            swatch.rightClicked.connect(lambda c=hexcolor: self.set_secondary(QColor(c)))
            grid.addWidget(swatch, i // 10, i % 10)
        layout.addWidget(grid_widget)

        more_btn = QToolButton()
        more_btn.setText("More…")
        more_btn.clicked.connect(self.open_color_dialog)
        layout.addWidget(more_btn)
        layout.addStretch()

    def set_primary(self, color: QColor):
        self.primary_color = QColor(color)
        self.indicator.set_colors(self.primary_color, self.secondary_color)
        self.primaryChanged.emit(self.primary_color)

    def set_secondary(self, color: QColor):
        self.secondary_color = QColor(color)
        self.indicator.set_colors(self.primary_color, self.secondary_color)
        self.secondaryChanged.emit(self.secondary_color)

    def swap_colors(self):
        self.primary_color, self.secondary_color = self.secondary_color, self.primary_color
        self.indicator.set_colors(self.primary_color, self.secondary_color)
        self.primaryChanged.emit(self.primary_color)
        self.secondaryChanged.emit(self.secondary_color)

    def open_color_dialog(self):
        dlg = QColorDialog(self.primary_color, self)
        dlg.setOption(QColorDialog.ShowAlphaChannel, True)
        if dlg.exec():
            self.set_primary(dlg.selectedColor())
