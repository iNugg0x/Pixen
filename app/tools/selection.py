from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath, QPolygonF

from app.tools.base_tool import BaseTool


class RectSelectionTool(BaseTool):
    name = "select-rect"

    def activate(self):
        super().activate()
        self._start = None
        self._end = None
        self._dragging_existing = False

    def mouse_press(self, pos: QPointF, event):
        sel = self.ctx.canvas.selection
        if sel is not None and sel.get("rect") and sel["rect"].contains(pos):
            self._dragging_existing = True
            self._drag_origin = pos
            self._sel_origin_rect = QRectF(sel["rect"])
            return
        self._dragging_existing = False
        self._start = pos
        self._end = pos

    def mouse_move(self, pos: QPointF, event):
        if self._dragging_existing:
            delta = pos - self._drag_origin
            new_rect = self._sel_origin_rect.translated(delta)
            self.ctx.canvas.selection["rect"] = new_rect
            self.ctx.canvas.update()
            return
        if self._start is None:
            return
        self._end = pos
        self.ctx.canvas.update()

    def mouse_release(self, pos: QPointF, event):
        if self._dragging_existing:
            self._dragging_existing = False
            return
        if self._start is None:
            return
        rect = QRectF(self._start, self._end).normalized()
        self.ctx.canvas.set_selection_rect(rect if rect.width() > 1 and rect.height() > 1 else None)
        self._start = None
        self._end = None
        self.ctx.canvas.update()

    def draw_overlay(self, painter: QPainter):
        canvas = self.ctx.canvas
        pen = QPen(QColor(60, 140, 255), 1, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        if self._start is not None and self._end is not None:
            r = QRectF(self._start, self._end).normalized()
            painter.drawRect(QRectF(canvas.doc_to_widget(r.topLeft()),
                                     canvas.doc_to_widget(r.bottomRight())))
        elif canvas.selection and canvas.selection.get("rect"):
            r = canvas.selection["rect"]
            painter.drawRect(QRectF(canvas.doc_to_widget(r.topLeft()),
                                     canvas.doc_to_widget(r.bottomRight())))


class FreeSelectionTool(BaseTool):
    """Lasso selection: freehand path, closed automatically on release."""
    name = "select-free"

    def activate(self):
        super().activate()
        self._points = []

    def mouse_press(self, pos: QPointF, event):
        self._points = [pos]

    def mouse_move(self, pos: QPointF, event):
        if self._points:
            self._points.append(pos)
            self.ctx.canvas.update()

    def mouse_release(self, pos: QPointF, event):
        if len(self._points) > 2:
            path = QPainterPath()
            path.moveTo(self._points[0])
            for p in self._points[1:]:
                path.lineTo(p)
            path.closeSubpath()
            self.ctx.canvas.set_selection_path(path)
        self._points = []
        self.ctx.canvas.update()

    def draw_overlay(self, painter: QPainter):
        if not self._points:
            return
        canvas = self.ctx.canvas
        pen = QPen(QColor(60, 140, 255), 1, Qt.DashLine)
        painter.setPen(pen)
        pts = [canvas.doc_to_widget(p) for p in self._points]
        painter.drawPolyline(QPolygonF(pts))
