from __future__ import annotations

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                                QStackedWidget, QWidget, QFormLayout, QComboBox,
                                QCheckBox, QSpinBox, QDoubleSpinBox, QDialogButtonBox,
                                QLabel)

from app.settings.settings_manager import SettingsManager


class SettingsDialog(QDialog):
    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings")
        self.resize(520, 380)

        layout = QHBoxLayout(self)
        self.categories = QListWidget()
        self.categories.addItems(["Appearance", "Canvas", "Tools", "Files"])
        self.categories.setFixedWidth(140)
        layout.addWidget(self.categories)

        right = QVBoxLayout()
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_appearance())
        self.stack.addWidget(self._build_canvas())
        self.stack.addWidget(self._build_tools())
        self.stack.addWidget(self._build_files())
        right.addWidget(self.stack)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        right.addWidget(buttons)
        layout.addLayout(right)

        self.categories.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.categories.setCurrentRow(0)

    def _build_appearance(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["system", "light", "dark"])
        self.theme_combo.setCurrentText(self.settings.get("appearance/theme"))
        form.addRow("Theme", self.theme_combo)

        self.icon_size_combo = QComboBox()
        self.icon_size_combo.addItems(["small", "medium", "large"])
        self.icon_size_combo.setCurrentText(self.settings.get("appearance/icon_size"))
        form.addRow("Icon size", self.icon_size_combo)

        self.density_combo = QComboBox()
        self.density_combo.addItems(["compact", "normal"])
        self.density_combo.setCurrentText(self.settings.get("appearance/density"))
        form.addRow("Interface density", self.density_combo)

        self.animations_check = QCheckBox("Enable subtle animations")
        self.animations_check.setChecked(self.settings.get("appearance/animations"))
        form.addRow("", self.animations_check)
        return w

    def _build_canvas(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.grid_check = QCheckBox("Show grid by default")
        self.grid_check.setChecked(self.settings.get("canvas/show_grid"))
        form.addRow("", self.grid_check)

        self.snap_grid_check = QCheckBox("Snap to grid")
        self.snap_grid_check.setChecked(self.settings.get("canvas/snap_to_grid"))
        form.addRow("", self.snap_grid_check)

        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(2, 200)
        self.grid_size_spin.setValue(self.settings.get("canvas/grid_size"))
        form.addRow("Grid size (px)", self.grid_size_spin)
        return w

    def _build_tools(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.default_size_spin = QSpinBox()
        self.default_size_spin.setRange(1, 200)
        self.default_size_spin.setValue(self.settings.get("tools/default_size"))
        form.addRow("Default brush size", self.default_size_spin)

        self.pressure_check = QCheckBox("Enable pen pressure sensitivity")
        self.pressure_check.setChecked(self.settings.get("tools/pen_pressure"))
        form.addRow("", self.pressure_check)

        self.smoothing_combo = QComboBox()
        self.smoothing_combo.addItems(["none", "low", "medium", "high"])
        self.smoothing_combo.setCurrentText(self.settings.get("tools/stroke_smoothing"))
        form.addRow("Stroke smoothing", self.smoothing_combo)
        return w

    def _build_files(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)
        self.default_format_combo = QComboBox()
        self.default_format_combo.addItems(["png", "jpg", "bmp", "webp"])
        self.default_format_combo.setCurrentText(self.settings.get("files/default_format"))
        form.addRow("Default export format", self.default_format_combo)

        self.jpg_quality_spin = QSpinBox()
        self.jpg_quality_spin.setRange(1, 100)
        self.jpg_quality_spin.setValue(self.settings.get("files/jpg_quality"))
        form.addRow("JPG quality", self.jpg_quality_spin)

        self.autosave_check = QCheckBox("Enable autosave")
        self.autosave_check.setChecked(self.settings.get("files/autosave_enabled"))
        form.addRow("", self.autosave_check)

        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(1, 60)
        self.autosave_interval_spin.setValue(self.settings.get("files/autosave_interval_min"))
        form.addRow("Autosave interval (min)", self.autosave_interval_spin)
        return w

    def accept(self):
        s = self.settings
        s.set("appearance/theme", self.theme_combo.currentText())
        s.set("appearance/icon_size", self.icon_size_combo.currentText())
        s.set("appearance/density", self.density_combo.currentText())
        s.set("appearance/animations", self.animations_check.isChecked())
        s.set("canvas/show_grid", self.grid_check.isChecked())
        s.set("canvas/snap_to_grid", self.snap_grid_check.isChecked())
        s.set("canvas/grid_size", self.grid_size_spin.value())
        s.set("tools/default_size", self.default_size_spin.value())
        s.set("tools/pen_pressure", self.pressure_check.isChecked())
        s.set("tools/stroke_smoothing", self.smoothing_combo.currentText())
        s.set("files/default_format", self.default_format_combo.currentText())
        s.set("files/jpg_quality", self.jpg_quality_spin.value())
        s.set("files/autosave_enabled", self.autosave_check.isChecked())
        s.set("files/autosave_interval_min", self.autosave_interval_spin.value())
        super().accept()
