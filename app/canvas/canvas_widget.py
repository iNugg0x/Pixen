from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QRectF, QRect, Signal, QMimeData
from PySide6.QtGui import (QPainter, QColor, QPixmap, QImage, QPen, QBrush,
                            QPainterPath, QCursor, QWheelEvent, QDragEnterEvent,
                            QDropEvent, QTabletEvent)
from PySide6.QtWidgets import QWidget, QSizePolicy

from app.canvas.document import Document
from app.history.undo_stack import HistoryManager
from app.tools.tool_manager import ToolManager


CHECKER_LIGHT = QColor(235, 235, 235)
CHECKER_DARK = QColor(210, 210, 210)


def make_checker_brush(size: int = 12) -> QBrush:
    pm = QPixmap(size * 2, size * 2)
    pm.fill(CHECKER_LIGHT)
    p = QPainter(pm)
    p.fillRect(0, 0, size, size, CHECKER_DARK)
    p.fillRect(size, size, size, size, CHECKER_DARK)
    p.end()
    return QBrush(pm)


class CanvasWidget(QWidget):
    zoomChanged = Signal(float)
    cursorMoved = Signal(int, int)
    selectionChanged = Signal(object)
    documentModified = Signal()
    layersChanged = Signal()

    def __init__(self, document: Document, parent=None):
        super().__init__(parent)
        self.document = document
        self.history = HistoryManager()
        self.tools = ToolManager(self)

        self.primary_color = QColor(Qt.black)
        self.secondary_color = QColor(Qt.white)

        self.zoom = 1.0
        self.pan = QPointF(0, 0)
        self.selection = None  # {"rect": QRectF} or {"path": QPainterPath}

        self.show_grid = False
        self.grid_size = 20
        self.snap_to_grid = False

        self._space_panning = False
        self._pan_last = None
        self._checker_brush = make_checker_brush()
        self.hover_widget_pos = None  # widget-space cursor pos; used for
                                       # the brush-size preview ring

        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAttribute(Qt.WA_TabletTracking, True)

    # -- coordinate mapping --------------------------------------------
    def doc_to_widget(self, p: QPointF) -> QPointF:
        origin = self._doc_origin()
        return QPointF(origin.x() + p.x() * self.zoom, origin.y() + p.y() * self.zoom)

    def widget_to_doc(self, p) -> QPointF:
        origin = self._doc_origin()
        return QPointF((p.x() - origin.x()) / self.zoom, (p.y() - origin.y()) / self.zoom)

    def _doc_origin(self) -> QPointF:
        w = self.width() - self.document.width * self.zoom
        h = self.height() - self.document.height * self.zoom
        base = QPointF(max(w / 2, 0), max(h / 2, 0))
        return base + self.pan

    # -- painting ---------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), self.palette().window())

        origin = self._doc_origin()
        target = QRectF(origin, QPointF(origin.x() + self.document.width * self.zoom,
                                         origin.y() + self.document.height * self.zoom))

        painter.save()
        painter.setClipRect(target)
        painter.fillRect(target, self._checker_brush)
        painter.restore()

        composited = self.document.render()
        painter.setRenderHint(QPainter.SmoothPixmapTransform, self.zoom < 1.0)
        painter.drawImage(target, composited)

        if self.show_grid:
            self._draw_grid(painter, target)

        # border
        painter.setPen(QPen(QColor(120, 120, 120), 1))
        painter.drawRect(target)

        # selection marquee
        if self.selection:
            self._draw_selection(painter)

        if self.tools.active_tool:
            self.tools.active_tool.draw_overlay(painter)

        painter.end()

    def _draw_grid(self, painter: QPainter, target: QRectF):
        painter.save()
        painter.setClipRect(target)
        pen = QPen(QColor(160, 160, 160, 120), 1)
        painter.setPen(pen)
        step = self.grid_size * self.zoom
        if step >= 4:
            x = target.left()
            while x <= target.right():
                painter.drawLine(QPointF(x, target.top()), QPointF(x, target.bottom()))
                x += step
            y = target.top()
            while y <= target.bottom():
                painter.drawLine(QPointF(target.left(), y), QPointF(target.right(), y))
                y += step
        painter.restore()

    def _draw_selection(self, painter: QPainter):
        pen = QPen(QColor(60, 140, 255), 1, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        if "rect" in self.selection and self.selection["rect"] is not None:
            r = self.selection["rect"]
            tl = self.doc_to_widget(r.topLeft())
            br = self.doc_to_widget(r.bottomRight())
            painter.drawRect(QRectF(tl, br))
        elif "path" in self.selection and self.selection["path"] is not None:
            path = self.selection["path"]
            scaled = QPainterPath()
            scaled.addPolygon(path.toFillPolygon())
            painter.save()
            origin = self._doc_origin()
            painter.translate(origin)
            painter.scale(self.zoom, self.zoom)
            painter.drawPath(path)
            painter.restore()

    # -- selection API ------------------------------------------------
    def set_selection_rect(self, rect):
        self.selection = {"rect": rect} if rect else None
        self.selectionChanged.emit(self.selection)
        self.update()

    def set_selection_path(self, path):
        self.selection = {"path": path}
        self.selectionChanged.emit(self.selection)
        self.update()

    def clear_selection(self):
        self.selection = None
        self.selectionChanged.emit(None)
        self.update()

    # -- mutation helpers used by tools -------------------------------
    def mark_layer_dirty(self, region: QRectF = None):
        """Tell the canvas the active layer's pixels changed.

        If `region` (a QRectF in *document* coordinates) is given, only
        that area is re-composited and repainted -- this is the fast path
        used by pencil/brush/eraser while dragging, so a stroke on a large
        canvas doesn't force a full multi-layer recomposite + full-widget
        repaint on every mouse-move event. Without a region, falls back to
        a full recomposite (used for one-off edits like fill or a
        committed shape, where the extra cost only happens once).
        """
        self.document.dirty = True
        if region is None:
            self.document.invalidate()
            self.update()
            return

        doc_rect = region.toAlignedRect().adjusted(-2, -2, 2, 2)
        self.document.composite_region(doc_rect)

        top_left = self.doc_to_widget(QPointF(doc_rect.left(), doc_rect.top()))
        bottom_right = self.doc_to_widget(QPointF(doc_rect.right(), doc_rect.bottom()))
        widget_rect = QRectF(top_left, bottom_right).toAlignedRect().adjusted(-2, -2, 2, 2)
        self.update(widget_rect)

    def commit_stroke(self):
        self.documentModified.emit()
        self.update()

    def set_primary_color(self, color: QColor):
        self.primary_color = QColor(color)

    def set_secondary_color(self, color: QColor):
        self.secondary_color = QColor(color)

    # -- zoom / pan -----------------------------------------------------
    def set_zoom(self, value: float, anchor=None):
        value = max(0.02, min(value, 32.0))
        if anchor is not None:
            before = self.widget_to_doc(anchor)
        self.zoom = value
        if anchor is not None:
            after = self.doc_to_widget(before)
            self.pan += anchor - after
        self.zoomChanged.emit(self.zoom)
        self.update()

    def zoom_to_fit(self):
        margin = 40
        if self.document.width == 0 or self.document.height == 0:
            return
        zx = (self.width() - margin) / self.document.width
        zy = (self.height() - margin) / self.document.height
        self.pan = QPointF(0, 0)
        self.set_zoom(max(0.02, min(zx, zy)))

    # -- events -----------------------------------------------------
    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 1 / 1.15
            self.set_zoom(self.zoom * factor, anchor=event.position())
        else:
            self.pan += QPointF(0, event.angleDelta().y() / 3)
            self.update()

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.MiddleButton or (
                event.button() == Qt.LeftButton and self._space_panning):
            self._pan_last = event.position()
            return
        pos = self.widget_to_doc(event.position())
        pos = self._maybe_snap(pos)
        if self.tools.active_tool:
            self.tools.active_tool.mouse_press(pos, event)
        self.update()

    def mouseMoveEvent(self, event):
        old_hover = self.hover_widget_pos
        self.hover_widget_pos = event.position()
        if old_hover is None:
            self.update()  # brush-size ring just appeared, needs a repaint
        pos = self.widget_to_doc(event.position())
        self.cursorMoved.emit(int(pos.x()), int(pos.y()))
        if self._pan_last is not None:
            delta = event.position() - self._pan_last
            self.pan += delta
            self._pan_last = event.position()
            self.update()
            return
        pos = self._maybe_snap(pos)
        if self.tools.active_tool:
            # Every tool already triggers exactly the repaint it needs
            # from within mouse_move -- a scoped `mark_layer_dirty(rect)`
            # for stroke/pixel edits, or a plain `update()` for overlay-
            # only feedback like a shape/selection preview. Adding an
            # unconditional full-widget update() here on top of that (the
            # previous behavior) silently widened every such repaint back
            # out to the whole canvas on every mouse-move event, which
            # defeated the point of the scoped updates during dragging.
            self.tools.active_tool.mouse_move(pos, event)
        elif self.hover_widget_pos is not None:
            self.update()  # no active tool: still need the cursor to move

    def mouseReleaseEvent(self, event):
        if self._pan_last is not None and event.button() in (Qt.MiddleButton, Qt.LeftButton):
            self._pan_last = None
            return
        pos = self.widget_to_doc(event.position())
        pos = self._maybe_snap(pos)
        if self.tools.active_tool:
            self.tools.active_tool.mouse_release(pos, event)
        self.update()

    def tabletEvent(self, event: QTabletEvent):
        # Pressure-aware input: modulate the active stroke tool's size via
        # pressure when supported; falls back silently on non-pen devices.
        tool = self.tools.active_tool
        if tool is not None and hasattr(tool, "size") and event.pointerType().name == "Pen":
            base = getattr(tool, "_base_size", None)
            if base is None:
                tool._base_size = tool.size
                base = tool.size
            pressure = max(0.15, event.pressure())
            tool.size = max(1, base * pressure)
        event.ignore()  # let Qt also synthesize the mouse event

    def leaveEvent(self, event):
        self.hover_widget_pos = None
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            self._space_panning = True
            self.setCursor(Qt.OpenHandCursor)
        if self.tools.active_tool:
            self.tools.active_tool.key_press(event)
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Space:
            self._space_panning = False
            self.tools.set_active(self.tools.active_tool.name)  # restore cursor
        super().keyReleaseEvent(event)

    def _maybe_snap(self, pos: QPointF) -> QPointF:
        if self.snap_to_grid and self.grid_size > 0:
            g = self.grid_size
            return QPointF(round(pos.x() / g) * g, round(pos.y() / g) * g)
        return pos

    # -- drag & drop ----------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path:
                self.add_image_as_layer(path, event.position())
        event.acceptProposedAction()

    def add_image_as_layer(self, path: str, drop_pos=None):
        img = QImage(path)
        if img.isNull():
            return
        self.history.push(self.document, "add image")
        from app.canvas.document import Layer
        import os
        layer = Layer(image=img.convertToFormat(QImage.Format_ARGB32_Premultiplied),
                      name=os.path.basename(path))
        self.document.layers.insert(self.document.active_layer_index + 1, layer)
        self.document.active_layer_index += 1
        self.layersChanged.emit()
        self.commit_stroke()
