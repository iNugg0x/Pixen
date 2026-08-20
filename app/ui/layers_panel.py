from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                                QListWidgetItem, QToolButton, QSlider, QLabel,
                                QAbstractItemView)


class LayersPanel(QWidget):
    layerSelected = Signal(int)
    addLayer = Signal()
    removeLayer = Signal()
    duplicateLayer = Signal()
    moveLayer = Signal(int, int)  # from, to
    visibilityToggled = Signal(int, bool)
    opacityChanged = Signal(int, float)
    renameLayer = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        header = QLabel("Layers")
        header.setStyleSheet("font-weight: 600;")
        layout.addWidget(header)

        self.list = QListWidget()
        self.list.setDragDropMode(QAbstractItemView.InternalMove)
        self.list.currentRowChanged.connect(self._on_row_changed)
        self.list.model().rowsMoved.connect(self._on_rows_moved)
        self.list.itemChanged.connect(self._on_item_changed)
        self.list.itemDoubleClicked.connect(self._on_double_click)
        layout.addWidget(self.list)

        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Opacity"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        opacity_row.addWidget(self.opacity_slider)
        layout.addLayout(opacity_row)

        btn_row = QHBoxLayout()
        self.add_btn = QToolButton(text="+")
        self.remove_btn = QToolButton(text="–")
        self.dup_btn = QToolButton(text="⧉")
        self.up_btn = QToolButton(text="↑")
        self.down_btn = QToolButton(text="↓")
        for b in (self.add_btn, self.remove_btn, self.dup_btn, self.up_btn, self.down_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        self.add_btn.clicked.connect(self.addLayer.emit)
        self.remove_btn.clicked.connect(self.removeLayer.emit)
        self.dup_btn.clicked.connect(self.duplicateLayer.emit)
        self.up_btn.clicked.connect(lambda: self._nudge(-1))
        self.down_btn.clicked.connect(lambda: self._nudge(1))

        self._suspend_signals = False

    def _nudge(self, direction: int):
        row = self.list.currentRow()
        new_row = row + direction
        if 0 <= new_row < self.list.count():
            self.moveLayer.emit(row, new_row)

    def _on_row_changed(self, row: int):
        if not self._suspend_signals and row >= 0:
            self.layerSelected.emit(row)

    def _on_rows_moved(self, parent, start, end, dest, row):
        target = row if row < start else row - 1
        self.moveLayer.emit(start, target)

    def _on_item_changed(self, item: QListWidgetItem):
        if self._suspend_signals:
            return
        row = self.list.row(item)
        self.visibilityToggled.emit(row, item.checkState() == Qt.Checked)

    def _on_double_click(self, item: QListWidgetItem):
        row = self.list.row(item)
        self.list.editItem(item)
        # renameLayer emitted after edit finishes via itemChanged text delta;
        # kept simple: rely on caller re-reading list text on save.

    def _on_opacity_changed(self, value: int):
        row = self.list.currentRow()
        if row >= 0:
            self.opacityChanged.emit(row, value / 100.0)

    # -- populate from document ------------------------------------
    def refresh(self, document):
        self._suspend_signals = True
        self.list.clear()
        for layer in reversed(document.layers):
            item = QListWidgetItem(layer.name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsEditable)
            item.setCheckState(Qt.Checked if layer.visible else Qt.Unchecked)
            self.list.addItem(item)
        active_from_top = len(document.layers) - 1 - document.active_layer_index
        self.list.setCurrentRow(active_from_top)
        active_opacity = document.layers[document.active_layer_index].opacity
        self.opacity_slider.setValue(int(active_opacity * 100))
        self._suspend_signals = False

    def display_row_to_layer_index(self, row: int, layer_count: int) -> int:
        return layer_count - 1 - row
