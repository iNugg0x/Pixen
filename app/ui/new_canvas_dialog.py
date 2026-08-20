from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                                QComboBox, QSpinBox, QDoubleSpinBox, QDialogButtonBox,
                                QLabel, QRadioButton, QButtonGroup, QCheckBox, QWidget)

from app.canvas.paper_sizes import PAPER_SIZES_MM, DPI_PRESETS, unit_to_px, paper_size_px


class NewCanvasDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Drawing")
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.size_combo = QComboBox()
        self.size_combo.addItems(list(PAPER_SIZES_MM.keys()) + ["Custom"])
        self.size_combo.setCurrentText("A4")
        form.addRow("Paper size", self.size_combo)

        orientation_row = QHBoxLayout()
        self.portrait_radio = QRadioButton("Portrait")
        self.landscape_radio = QRadioButton("Landscape")
        self.portrait_radio.setChecked(True)
        group = QButtonGroup(self)
        group.addButton(self.portrait_radio)
        group.addButton(self.landscape_radio)
        orientation_row.addWidget(self.portrait_radio)
        orientation_row.addWidget(self.landscape_radio)
        form.addRow("Orientation", orientation_row)

        dims_row = QHBoxLayout()
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(1, 20000)
        self.width_spin.setValue(210)
        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(1, 20000)
        self.height_spin.setValue(297)
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["mm", "cm", "in", "px"])
        dims_row.addWidget(self.width_spin)
        dims_row.addWidget(QLabel("×"))
        dims_row.addWidget(self.height_spin)
        dims_row.addWidget(self.unit_combo)
        form.addRow("Dimensions", dims_row)

        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems([str(d) for d in DPI_PRESETS] + ["Custom"])
        self.dpi_combo.setCurrentText("96")
        self.dpi_custom = QSpinBox()
        self.dpi_custom.setRange(1, 2400)
        self.dpi_custom.setValue(96)
        self.dpi_custom.setVisible(False)
        dpi_row = QHBoxLayout()
        dpi_row.addWidget(self.dpi_combo)
        dpi_row.addWidget(self.dpi_custom)
        form.addRow("DPI", dpi_row)

        self.margin_combo = QComboBox()
        self.margin_combo.addItems(["0 mm", "5 mm", "10 mm", "15 mm", "20 mm", "Custom"])
        form.addRow("Margins (visual guide)", self.margin_combo)

        self.transparent_check = QCheckBox("Transparent background")
        form.addRow("", self.transparent_check)

        layout.addLayout(form)

        self.preview_label = QLabel()
        self.preview_label.setStyleSheet("color: #888;")
        layout.addWidget(self.preview_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.size_combo.currentTextChanged.connect(self._on_paper_changed)
        self.landscape_radio.toggled.connect(self._on_paper_changed)
        self.dpi_combo.currentTextChanged.connect(self._on_dpi_changed)
        self.width_spin.valueChanged.connect(self._update_preview)
        self.height_spin.valueChanged.connect(self._update_preview)
        self.unit_combo.currentTextChanged.connect(self._on_paper_changed)
        self.dpi_custom.valueChanged.connect(self._update_preview)

        self._on_paper_changed()

    def _on_dpi_changed(self, text):
        self.dpi_custom.setVisible(text == "Custom")
        self._update_preview()

    def _on_paper_changed(self, *_):
        name = self.size_combo.currentText()
        is_custom = name == "Custom"
        self.width_spin.setEnabled(is_custom or self.unit_combo.currentText() == "px")
        self.height_spin.setEnabled(True)
        if not is_custom:
            w_mm, h_mm = PAPER_SIZES_MM[name]
            if self.landscape_radio.isChecked():
                w_mm, h_mm = h_mm, w_mm
            unit = self.unit_combo.currentText()
            dpi = self._current_dpi()
            from app.canvas.paper_sizes import px_to_unit, mm_to_px
            if unit == "mm":
                self.width_spin.setValue(w_mm)
                self.height_spin.setValue(h_mm)
            elif unit == "cm":
                self.width_spin.setValue(w_mm / 10)
                self.height_spin.setValue(h_mm / 10)
            elif unit == "in":
                self.width_spin.setValue(w_mm / 25.4)
                self.height_spin.setValue(h_mm / 25.4)
            else:
                self.width_spin.setValue(mm_to_px(w_mm, dpi))
                self.height_spin.setValue(mm_to_px(h_mm, dpi))
        self._update_preview()

    def _current_dpi(self) -> int:
        text = self.dpi_combo.currentText()
        return self.dpi_custom.value() if text == "Custom" else int(text)

    def _update_preview(self, *_):
        w, h = self.result_pixel_size()
        mp = (w * h) / 1_000_000
        self.preview_label.setText(f"{w} × {h} px  (~{mp:.1f} MP)")

    def result_pixel_size(self):
        unit = self.unit_combo.currentText()
        dpi = self._current_dpi()
        w = unit_to_px(self.width_spin.value(), unit, dpi)
        h = unit_to_px(self.height_spin.value(), unit, dpi)
        return max(1, w), max(1, h)

    def get_values(self) -> dict:
        w, h = self.result_pixel_size()
        return {
            "width": w,
            "height": h,
            "dpi": self._current_dpi(),
            "transparent": self.transparent_check.isChecked(),
            "name": self.size_combo.currentText(),
        }
