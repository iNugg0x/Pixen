from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QSettings
from PySide6.QtGui import QAction, QKeySequence, QColor, QCloseEvent
from PySide6.QtWidgets import (QMainWindow, QDockWidget, QFileDialog, QMessageBox,
                                QVBoxLayout, QWidget, QLabel, QInputDialog)

from app.canvas.document import Document
from app.canvas.canvas_widget import CanvasWidget
from app.ui.toolbar import build_toolbar, refresh_toolbar_icons, ICON_COLOR_LIGHT, ICON_COLOR_DARK
from app.ui.color_panel import ColorPanel
from app.ui.layers_panel import LayersPanel
from app.ui.status_bar import AppStatusBar
from app.ui.new_canvas_dialog import NewCanvasDialog
from app.ui.settings_dialog import SettingsDialog
from app.settings.settings_manager import SettingsManager
from app.shortcuts.shortcut_manager import ShortcutManager
from app.files import io as file_io
from app.printing.print_manager import print_document, preview_document

APP_NAME = "Pixen"
RECENT_KEY = "recent/files"
MAX_RECENT = 8


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = SettingsManager()
        self.shortcuts = ShortcutManager()
        self.setWindowTitle(APP_NAME)
        self.resize(1280, 820)

        self.document = Document(*self._default_size(), name="Untitled")
        self.canvas = CanvasWidget(self.document)
        self.setCentralWidget(self.canvas)

        self._build_docks()
        self._build_menus()
        self.toolbar = build_toolbar(self)
        self.addToolBar(self.toolbar)
        self.status = AppStatusBar()
        self.setStatusBar(self.status)

        self._wire_canvas_signals()
        self._apply_theme(self.settings.get("appearance/theme"))
        self._apply_stroke_settings()
        self._refresh_all()

        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._autosave)
        self._configure_autosave()

        self._ui_mode = "normal"

    # -- setup -----------------------------------------------------
    def _default_size(self):
        from app.canvas.paper_sizes import paper_size_px
        w, h = paper_size_px("A4", 96)
        return w, h

    def _build_docks(self):
        self.color_panel = ColorPanel()
        color_dock = QDockWidget("Colors", self)
        color_dock.setObjectName("colorsDock")
        color_dock.setWidget(self.color_panel)
        color_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.TopDockWidgetArea, color_dock)
        self.color_dock = color_dock

        self.layers_panel = LayersPanel()
        layers_dock = QDockWidget("Layers", self)
        layers_dock.setObjectName("layersDock")
        layers_dock.setWidget(self.layers_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, layers_dock)
        self.layers_dock = layers_dock

        self.color_panel.primaryChanged.connect(self._on_primary_changed)
        self.color_panel.secondaryChanged.connect(self._on_secondary_changed)

        self.layers_panel.addLayer.connect(self._add_layer)
        self.layers_panel.removeLayer.connect(self._remove_layer)
        self.layers_panel.duplicateLayer.connect(self._duplicate_layer)
        self.layers_panel.moveLayer.connect(self._move_layer)
        self.layers_panel.layerSelected.connect(self._select_layer)
        self.layers_panel.visibilityToggled.connect(self._toggle_layer_visibility)
        self.layers_panel.opacityChanged.connect(self._set_layer_opacity)

    def _wire_canvas_signals(self):
        self.canvas.cursorMoved.connect(self.status.set_cursor_pos)
        self.canvas.zoomChanged.connect(self.status.set_zoom)
        self.canvas.selectionChanged.connect(lambda sel: self.status.set_selection(
            sel.get("rect") if sel else None))
        self.canvas.documentModified.connect(self._on_document_modified)
        self.canvas.layersChanged.connect(lambda: self.layers_panel.refresh(self.document))

    # -- menus -----------------------------------------------------
    def _act(self, text, slot, shortcut_id=None, checkable=False):
        action = QAction(text, self)
        if shortcut_id:
            action.setShortcut(QKeySequence(self.shortcuts.get(shortcut_id)))
        action.setCheckable(checkable)
        action.triggered.connect(slot)
        return action

    def _build_menus(self):
        menubar = self.menuBar()

        file_menu = menubar.addMenu("&File")
        file_menu.addAction(self._act("New…", self.new_document, "new"))
        file_menu.addAction(self._act("Open…", self.open_document, "open"))
        self.recent_menu = file_menu.addMenu("Open Recent")
        self._refresh_recent_menu()
        file_menu.addSeparator()
        file_menu.addAction(self._act("Save", self.save_document, "save"))
        file_menu.addAction(self._act("Save As…", self.save_document_as, "save_as"))
        export_menu = file_menu.addMenu("Quick Export")
        for fmt in ("PNG", "JPG", "BMP", "WEBP"):
            export_menu.addAction(self._act(fmt, lambda checked=False, f=fmt: self.quick_export(f)))
        file_menu.addSeparator()
        file_menu.addAction(self._act("Print Preview…", self.print_preview))
        file_menu.addAction(self._act("Print…", self.print_now, "print"))
        file_menu.addSeparator()
        file_menu.addAction(self._act("Settings…", self.open_settings))
        file_menu.addSeparator()
        file_menu.addAction(self._act("Exit", self.close))

        edit_menu = menubar.addMenu("&Edit")
        self.undo_action = self._act("Undo", self.undo, "undo")
        self.redo_action = self._act("Redo", self.redo, "redo")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        edit_menu.addSeparator()
        edit_menu.addAction(self._act("Cut", self.cut_selection, "cut"))
        edit_menu.addAction(self._act("Copy", self.copy_selection, "copy"))
        edit_menu.addAction(self._act("Paste", self.paste_clipboard, "paste"))
        edit_menu.addAction(self._act("Duplicate", self.duplicate_selection, "duplicate"))
        edit_menu.addSeparator()
        edit_menu.addAction(self._act("Select All", self.select_all, "select_all"))
        edit_menu.addAction(self._act("Deselect", self.deselect, "deselect"))

        image_menu = menubar.addMenu("&Image")
        image_menu.addAction(self._act("Resize Canvas…", self.resize_canvas_dialog))
        image_menu.addAction(self._act("Add Image…", self.add_image))
        image_menu.addSeparator()
        image_menu.addAction(self._act("Flip Horizontal", lambda: self.flip_active_layer(True)))
        image_menu.addAction(self._act("Flip Vertical", lambda: self.flip_active_layer(False)))
        image_menu.addAction(self._act("Rotate 90° CW", lambda: self.rotate_active_layer(90)))
        image_menu.addAction(self._act("Rotate 90° CCW", lambda: self.rotate_active_layer(-90)))

        layer_menu = menubar.addMenu("&Layer")
        layer_menu.addAction(self._act("Add Layer", self._add_layer))
        layer_menu.addAction(self._act("Duplicate Layer", self._duplicate_layer))
        layer_menu.addAction(self._act("Delete Layer", self._remove_layer))

        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self._act("Zoom In", lambda: self.canvas.set_zoom(self.canvas.zoom * 1.25), "zoom_in"))
        view_menu.addAction(self._act("Zoom Out", lambda: self.canvas.set_zoom(self.canvas.zoom / 1.25), "zoom_out"))
        view_menu.addAction(self._act("Zoom to Fit", self.canvas.zoom_to_fit, "zoom_fit"))
        view_menu.addAction(self._act("Actual Size (100%)", lambda: self.canvas.set_zoom(1.0), "zoom_100"))
        view_menu.addSeparator()
        self.grid_action = self._act("Show Grid", self.toggle_grid, checkable=True)
        self.grid_action.setChecked(self.settings.get("canvas/show_grid"))
        self.canvas.show_grid = self.grid_action.isChecked()
        view_menu.addAction(self.grid_action)
        self.snap_action = self._act("Snap to Grid", self.toggle_snap, checkable=True)
        self.snap_action.setChecked(self.settings.get("canvas/snap_to_grid"))
        self.canvas.snap_to_grid = self.snap_action.isChecked()
        view_menu.addAction(self.snap_action)
        view_menu.addSeparator()
        mode_menu = view_menu.addMenu("Interface Mode")
        mode_menu.addAction(self._act("Normal", lambda: self.set_ui_mode("normal")))
        mode_menu.addAction(self._act("Compact", lambda: self.set_ui_mode("compact")))
        mode_menu.addAction(self._act("Canvas Only", lambda: self.set_ui_mode("canvas-only")))
        view_menu.addAction(self._act("Toggle Fullscreen", self.toggle_fullscreen, "fullscreen"))

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction(self._act("About", self.show_about))

    def _refresh_recent_menu(self):
        self.recent_menu.clear()
        qs = QSettings("Pixen", "Pixen")
        recent = qs.value(RECENT_KEY, [])
        recent = recent if isinstance(recent, list) else [recent] if recent else []
        for path in recent:
            self.recent_menu.addAction(self._act(path, lambda checked=False, p=path: self._open_path(p)))
        if not recent:
            empty = QAction("(no recent files)", self)
            empty.setEnabled(False)
            self.recent_menu.addAction(empty)

    def _add_recent(self, path: str):
        qs = QSettings("Pixen", "Pixen")
        recent = qs.value(RECENT_KEY, [])
        recent = recent if isinstance(recent, list) else [recent] if recent else []
        recent = [p for p in recent if p != path]
        recent.insert(0, path)
        qs.setValue(RECENT_KEY, recent[:MAX_RECENT])
        self._refresh_recent_menu()

    # -- tool wiring -------------------------------------------------
    def set_active_tool(self, name: str):
        self.canvas.tools.set_active(name)

    def set_tool_size(self, value: int):
        tool = self.canvas.tools.active_tool
        if hasattr(tool, "size"):
            tool.size = value

    def set_tool_opacity(self, value: int):
        tool = self.canvas.tools.active_tool
        if hasattr(tool, "opacity"):
            tool.opacity = value / 100.0

    def _apply_stroke_settings(self):
        """Push the stroke-smoothing preference into every pencil/brush/
        eraser tool instance. Called on startup and whenever Settings is
        saved, so a mid-drawing change takes effect immediately."""
        smoothing = self.settings.get("tools/stroke_smoothing")
        for tool in self.canvas.tools.tools.values():
            if hasattr(tool, "smoothing"):
                tool.smoothing = smoothing

    # -- color wiring --------------------------------------------------
    def _on_primary_changed(self, color: QColor):
        self.canvas.set_primary_color(color)

    def _on_secondary_changed(self, color: QColor):
        self.canvas.set_secondary_color(color)

    # -- layer actions -------------------------------------------------
    def _add_layer(self):
        self.canvas.history.push(self.document, "add layer")
        self.document.add_layer()
        self._refresh_all()

    def _remove_layer(self):
        self.canvas.history.push(self.document, "delete layer")
        self.document.remove_layer()
        self._refresh_all()

    def _duplicate_layer(self):
        self.canvas.history.push(self.document, "duplicate layer")
        self.document.duplicate_layer()
        self._refresh_all()

    def _move_layer(self, from_row: int, to_row: int):
        n = len(self.document.layers)
        from_idx = self.layers_panel.display_row_to_layer_index(from_row, n)
        to_idx = self.layers_panel.display_row_to_layer_index(to_row, n)
        self.canvas.history.push(self.document, "reorder layers")
        self.document.move_layer(from_idx, to_idx)
        self._refresh_all()

    def _select_layer(self, row: int):
        n = len(self.document.layers)
        idx = self.layers_panel.display_row_to_layer_index(row, n)
        if 0 <= idx < n:
            self.document.active_layer_index = idx
            self.canvas.update()

    def _toggle_layer_visibility(self, row: int, visible: bool):
        n = len(self.document.layers)
        idx = self.layers_panel.display_row_to_layer_index(row, n)
        self.document.layers[idx].visible = visible
        self.canvas.update()

    def _set_layer_opacity(self, row: int, opacity: float):
        n = len(self.document.layers)
        idx = self.layers_panel.display_row_to_layer_index(row, n)
        self.document.layers[idx].opacity = opacity
        self.canvas.update()

    # -- selection / clipboard -----------------------------------------
    def _selected_region_image(self):
        sel = self.canvas.selection
        if not sel or not sel.get("rect"):
            return None, None
        rect = sel["rect"].toRect()
        img = self.document.active_layer.image.copy(rect)
        return img, rect

    def copy_selection(self):
        from PySide6.QtWidgets import QApplication
        img, rect = self._selected_region_image()
        if img is not None:
            QApplication.clipboard().setImage(img)

    def cut_selection(self):
        from PySide6.QtGui import QPainter
        img, rect = self._selected_region_image()
        if img is None:
            return
        self.copy_selection()
        self.canvas.history.push(self.document, "cut")
        painter = QPainter(self.document.active_layer.image)
        painter.setCompositionMode(QPainter.CompositionMode_Clear)
        painter.fillRect(rect, Qt.transparent)
        painter.end()
        self.canvas.mark_layer_dirty()
        self.canvas.commit_stroke()

    def paste_clipboard(self):
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QPainter
        img = QApplication.clipboard().image()
        if img.isNull():
            return
        self.canvas.history.push(self.document, "paste")
        layer = self.document.active_layer
        painter = QPainter(layer.image)
        painter.drawImage(10, 10, img)
        painter.end()
        self.canvas.mark_layer_dirty()
        self.canvas.commit_stroke()

    def duplicate_selection(self):
        img, rect = self._selected_region_image()
        if img is None:
            return
        from PySide6.QtGui import QPainter
        self.canvas.history.push(self.document, "duplicate selection")
        painter = QPainter(self.document.active_layer.image)
        painter.drawImage(rect.x() + 10, rect.y() + 10, img)
        painter.end()
        self.canvas.mark_layer_dirty()
        self.canvas.commit_stroke()

    def select_all(self):
        from PySide6.QtCore import QRectF
        self.canvas.set_selection_rect(QRectF(0, 0, self.document.width, self.document.height))

    def deselect(self):
        self.canvas.clear_selection()

    # -- undo/redo -------------------------------------------------
    def undo(self):
        if self.canvas.history.undo(self.document):
            self._refresh_all()

    def redo(self):
        if self.canvas.history.redo(self.document):
            self._refresh_all()

    # -- image operations ------------------------------------------
    def flip_active_layer(self, horizontal: bool):
        self.canvas.history.push(self.document, "flip")
        layer = self.document.active_layer
        layer.image = layer.image.mirrored(horizontal, not horizontal)
        self.canvas.mark_layer_dirty()
        self.canvas.commit_stroke()

    def rotate_active_layer(self, degrees: int):
        from PySide6.QtGui import QTransform
        self.canvas.history.push(self.document, "rotate")
        layer = self.document.active_layer
        layer.image = layer.image.transformed(QTransform().rotate(degrees), Qt.SmoothTransformation)
        self.canvas.mark_layer_dirty()
        self.canvas.commit_stroke()

    def resize_canvas_dialog(self):
        w, ok1 = QInputDialog.getInt(self, "Resize Canvas", "Width (px):", self.document.width, 1, 20000)
        if not ok1:
            return
        h, ok2 = QInputDialog.getInt(self, "Resize Canvas", "Height (px):", self.document.height, 1, 20000)
        if not ok2:
            return
        self.canvas.history.push(self.document, "resize canvas")
        self.document.resize_canvas(w, h, anchor="center", resize_content=False)
        self.canvas.zoom_to_fit()
        self._refresh_all()

    def add_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Add Image", "",
                                               "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self.canvas.add_image_as_layer(path)
            self._refresh_all()

    # -- document lifecycle ----------------------------------------
    def new_document(self):
        if not self._confirm_discard_changes():
            return
        dlg = NewCanvasDialog(self)
        if dlg.exec():
            values = dlg.get_values()
            self.document = Document(values["width"], values["height"], values["dpi"],
                                      transparent=values["transparent"], name="Untitled")
            self.canvas.document = self.document
            self.canvas.history.clear()
            self.canvas.clear_selection()
            self.canvas.zoom_to_fit()
            self._refresh_all()

    def open_document(self):
        if not self._confirm_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open", "",
            "All Supported (*.qpaint *.png *.jpg *.jpeg *.bmp *.webp);;Pixen Project (*.qpaint);;Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if path:
            self._open_path(path)

    def _open_path(self, path: str):
        try:
            self.document = file_io.open_document(path)
        except Exception as exc:
            QMessageBox.warning(self, APP_NAME, f"Could not open file:\n{exc}")
            return
        self.canvas.document = self.document
        self.canvas.history.clear()
        self.canvas.clear_selection()
        self.canvas.zoom_to_fit()
        self._refresh_all()
        self._add_recent(path)

    def save_document(self):
        if self.document.file_path is None:
            self.save_document_as()
            return
        file_io.save_document(self.document)
        self._add_recent(self.document.file_path)
        self._refresh_all()

    def save_document_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save As", f"{self.document.name}.qpaint",
            "Pixen Project (*.qpaint);;PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp);;WebP (*.webp)")
        if path:
            file_io.save_document(self.document, path)
            self._add_recent(path)
            self._refresh_all()

    def quick_export(self, fmt: str):
        ext = fmt.lower()
        path, _ = QFileDialog.getSaveFileName(self, f"Export {fmt}", f"{self.document.name}.{ext}",
                                               f"{fmt} (*.{ext})")
        if path:
            quality = self.settings.get("files/jpg_quality")
            file_io.save_raster(self.document, path, quality)

    def print_now(self):
        print_document(self.document, self)

    def print_preview(self):
        preview_document(self.document, self)

    # -- view ---------------------------------------------------------
    def toggle_grid(self, checked: bool):
        self.canvas.show_grid = checked
        self.settings.set("canvas/show_grid", checked)
        self.canvas.update()

    def toggle_snap(self, checked: bool):
        self.canvas.snap_to_grid = checked
        self.settings.set("canvas/snap_to_grid", checked)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def set_ui_mode(self, mode: str):
        self._ui_mode = mode
        if mode == "canvas-only":
            self.menuBar().setVisible(False)
            self.toolbar.setVisible(False)
            self.status.setVisible(False)
            self.color_dock.setVisible(False)
            self.layers_dock.setVisible(False)
        elif mode == "compact":
            self.menuBar().setVisible(True)
            self.toolbar.setVisible(True)
            self.status.setVisible(False)
            self.color_dock.setVisible(False)
            self.layers_dock.setVisible(True)
        else:
            self.menuBar().setVisible(True)
            self.toolbar.setVisible(True)
            self.status.setVisible(True)
            self.color_dock.setVisible(True)
            self.layers_dock.setVisible(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self._ui_mode == "canvas-only":
            self.set_ui_mode("normal")
        super().keyPressEvent(event)

    # -- settings / theme -----------------------------------------------
    def open_settings(self):
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            self._apply_theme(self.settings.get("appearance/theme"))
            self.canvas.show_grid = self.settings.get("canvas/show_grid")
            self.canvas.snap_to_grid = self.settings.get("canvas/snap_to_grid")
            self.canvas.grid_size = self.settings.get("canvas/grid_size")
            self._configure_autosave()
            self._apply_stroke_settings()
            self.canvas.update()

    def _apply_theme(self, theme: str):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if theme == "dark":
            app.setStyleSheet(_DARK_QSS)
            icon_color = ICON_COLOR_DARK
        elif theme == "light":
            app.setStyleSheet(_LIGHT_QSS)
            icon_color = ICON_COLOR_LIGHT
        else:
            app.setStyleSheet("")  # follow system
            icon_color = None  # derive from the current system palette

        # Toolbar icons are pre-rendered pixmaps, not QSS-styled text, so
        # they need to be explicitly redrawn in a color that matches the
        # new background -- otherwise dark icons can vanish against a
        # dark toolbar (and vice versa).
        if hasattr(self, "tool_actions"):
            refresh_toolbar_icons(self, icon_color)

    def _configure_autosave(self):
        enabled = self.settings.get("files/autosave_enabled")
        interval = self.settings.get("files/autosave_interval_min")
        self._autosave_timer.stop()
        if enabled:
            self._autosave_timer.start(int(interval * 60 * 1000))

    def _autosave(self):
        if not self.document.dirty:
            return
        autosave_dir = Path.home() / ".modernpaint" / "autosave"
        autosave_dir.mkdir(parents=True, exist_ok=True)
        path = autosave_dir / f"{self.document.name}_autosave.qpaint"
        try:
            file_io.save_native(self.document, str(path))
            self.document.dirty = True  # autosave shouldn't clear the "real" dirty flag
        except Exception:
            pass

    # -- misc ---------------------------------------------------------
    def show_about(self):
        QMessageBox.about(self, "About", f"{APP_NAME}\n\nA modern, minimal, local-first "
                           "paint application. No AI, no cloud, no accounts.")

    def _on_document_modified(self):
        self.document.dirty = True
        self._refresh_all()

    def _refresh_all(self):
        self.layers_panel.refresh(self.document)
        self.status.set_document_info(self.document.width, self.document.height,
                                       self.document.dpi, len(self.document.layers))
        self.undo_action.setEnabled(self.canvas.history.can_undo)
        self.redo_action.setEnabled(self.canvas.history.can_redo)
        title = self.document.name + (" *" if self.document.dirty else "")
        self.setWindowTitle(f"{title} — {APP_NAME}")

    def _confirm_discard_changes(self) -> bool:
        if not self.document.dirty:
            return True
        result = QMessageBox.question(
            self, APP_NAME, "You have unsaved changes. Save before continuing?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        if result == QMessageBox.Save:
            self.save_document()
            return not self.document.dirty
        return result == QMessageBox.Discard

    def closeEvent(self, event: QCloseEvent):
        if self._confirm_discard_changes():
            event.accept()
        else:
            event.ignore()


_LIGHT_QSS = """
QMainWindow, QDockWidget, QDialog { background: #fafafa; }
QToolBar { background: #f2f2f2; border: none; spacing: 4px; }
QStatusBar { background: #f2f2f2; }
QMenuBar { background: #f7f7f7; }
"""

_DARK_QSS = """
QMainWindow, QWidget { background: #1e1f22; color: #e6e6e6; }
QDockWidget { background: #1e1f22; color: #e6e6e6; }
QToolBar { background: #26272b; border: none; spacing: 4px; }
QStatusBar { background: #26272b; color: #ccc; }
QMenuBar { background: #26272b; color: #e6e6e6; }
QMenuBar::item:selected { background: #37383d; }
QMenu { background: #26272b; color: #e6e6e6; }
QMenu::item:selected { background: #37383d; }
QListWidget, QTextEdit, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background: #2a2b2f; color: #e6e6e6; border: 1px solid #3a3b40;
}
"""
