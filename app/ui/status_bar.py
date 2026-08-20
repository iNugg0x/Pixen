from __future__ import annotations

from PySide6.QtWidgets import QStatusBar, QLabel


class AppStatusBar(QStatusBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizeGripEnabled(False)

        self.dims_label = QLabel()
        self.dpi_label = QLabel()
        self.cursor_label = QLabel()
        self.zoom_label = QLabel()
        self.selection_label = QLabel()
        self.layers_label = QLabel()

        for w in (self.dims_label, self.dpi_label, self.cursor_label,
                  self.zoom_label, self.selection_label, self.layers_label):
            w.setStyleSheet("color: #777; padding: 0 8px;")
            self.addPermanentWidget(w)

    def set_document_info(self, width: int, height: int, dpi: int, layer_count: int):
        self.dims_label.setText(f"{width} × {height} px")
        self.dpi_label.setText(f"{dpi} DPI")
        self.layers_label.setText(f"{layer_count} layer{'s' if layer_count != 1 else ''}")

    def set_cursor_pos(self, x: int, y: int):
        self.cursor_label.setText(f"x {x}, y {y}")

    def set_zoom(self, zoom: float):
        self.zoom_label.setText(f"{int(zoom * 100)}%")

    def set_selection(self, rect):
        if rect is None:
            self.selection_label.setText("")
        else:
            self.selection_label.setText(f"sel {int(rect.width())} × {int(rect.height())}")
