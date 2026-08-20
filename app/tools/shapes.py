from __future__ import annotations

import math

from PySide6.QtCore import QPointF, Qt, QRectF, QLineF
from PySide6.QtGui import QPainter, QPen, QColor, QPolygonF

from app.tools.base_tool import BaseTool


class _ShapeTool(BaseTool):
    """Drag-to-define shape with live preview; committed to the layer on
    mouse release. Shift constrains proportions/angle, Alt draws from
    center where applicable."""

    stroke_width = 3
    fill_shape = False
    outline = True

    def activate(self):
        super().activate()
        self._start = None
        self._end = None
        self._shift = False
        self._alt = False

    def mouse_press(self, pos: QPointF, event):
        self._start = pos
        self._end = pos

    def mouse_move(self, pos: QPointF, event):
        if self._start is None:
            return
        self._shift = bool(event.modifiers() & Qt.ShiftModifier)
        self._alt = bool(event.modifiers() & Qt.AltModifier)
        self._end = pos
        self.ctx.canvas.update()

    def mouse_release(self, pos: QPointF, event):
        if self._start is None:
            return
        self._shift = bool(event.modifiers() & Qt.ShiftModifier)
        self._alt = bool(event.modifiers() & Qt.AltModifier)
        self._end = pos
        self.ctx.canvas.history.push(self.ctx.document, self.name)
        layer = self.ctx.document.active_layer
        painter = QPainter(layer.image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(QColor(self.ctx.primary_color), self.stroke_width,
                    Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen if self.outline else Qt.NoPen)
        painter.setBrush(QColor(self.ctx.secondary_color) if self.fill_shape else Qt.NoBrush)
        self._paint_shape(painter)
        painter.end()
        self._start = None
        self._end = None
        self.ctx.canvas.mark_layer_dirty()
        self.ctx.canvas.commit_stroke()

    def _rect(self) -> QRectF:
        r = QRectF(self._start, self._end).normalized()
        if self._shift:
            side = max(r.width(), r.height())
            r = QRectF(r.left(), r.top(), side, side)
        if self._alt:
            w, h = (r.width(), r.width()) if self._shift else (
                abs(self._end.x() - self._start.x()) * 2,
                abs(self._end.y() - self._start.y()) * 2)
            r = QRectF(self._start.x() - w / 2, self._start.y() - h / 2, w, h)
        return r

    def _paint_shape(self, painter: QPainter):
        raise NotImplementedError

    def draw_overlay(self, painter: QPainter):
        if self._start is None or self._end is None:
            return
        canvas = self.ctx.canvas
        pen = QPen(QColor(120, 170, 255), 1, Qt.DashLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        self._paint_preview(painter, canvas)

    def _paint_preview(self, painter: QPainter, canvas):
        # Default: reuse _rect mapped to screen coords
        pass


class LineTool(_ShapeTool):
    name = "line"

    def _paint_shape(self, painter: QPainter):
        start, end = self._start, self._end
        if self._shift:
            angle = math.degrees(math.atan2(end.y() - start.y(), end.x() - start.x()))
            snapped = round(angle / 45) * 45
            length = QLineF(start, end).length()
            rad = math.radians(snapped)
            end = QPointF(start.x() + length * math.cos(rad),
                           start.y() + length * math.sin(rad))
        painter.drawLine(start, end)

    def _paint_preview(self, painter: QPainter, canvas):
        s = canvas.doc_to_widget(self._start)
        e = canvas.doc_to_widget(self._end)
        if self._shift:
            angle = math.degrees(math.atan2(e.y() - s.y(), e.x() - s.x()))
            snapped = round(angle / 45) * 45
            length = QLineF(s, e).length()
            rad = math.radians(snapped)
            e = QPointF(s.x() + length * math.cos(rad), s.y() + length * math.sin(rad))
        painter.drawLine(s, e)


class RectangleTool(_ShapeTool):
    name = "rectangle"

    def _paint_shape(self, painter: QPainter):
        painter.drawRect(self._rect())

    def _paint_preview(self, painter: QPainter, canvas):
        r = self._rect()
        top_left = canvas.doc_to_widget(r.topLeft())
        bottom_right = canvas.doc_to_widget(r.bottomRight())
        painter.drawRect(QRectF(top_left, bottom_right))


class EllipseTool(_ShapeTool):
    name = "ellipse"

    def _paint_shape(self, painter: QPainter):
        painter.drawEllipse(self._rect())

    def _paint_preview(self, painter: QPainter, canvas):
        r = self._rect()
        top_left = canvas.doc_to_widget(r.topLeft())
        bottom_right = canvas.doc_to_widget(r.bottomRight())
        painter.drawEllipse(QRectF(top_left, bottom_right))


class PolygonTool(BaseTool):
    """Click to add vertices, double-click or Enter to close the shape."""
    name = "polygon"
    stroke_width = 3

    def activate(self):
        super().activate()
        self._points = []

    def mouse_press(self, pos: QPointF, event):
        if event.type().name == "MouseButtonDblClick" or (
                self._points and (pos - self._points[0]).manhattanLength() < 6):
            self._commit()
            return
        self._points.append(pos)
        self.ctx.canvas.update()

    def key_press(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Escape):
            if event.key() != Qt.Key_Escape:
                self._commit()
            self._points = []
            self.ctx.canvas.update()

    def _commit(self):
        if len(self._points) < 2:
            self._points = []
            return
        self.ctx.canvas.history.push(self.ctx.document, self.name)
        layer = self.ctx.document.active_layer
        painter = QPainter(layer.image)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen = QPen(QColor(self.ctx.primary_color), self.stroke_width,
                    Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawPolygon(QPolygonF(self._points))
        painter.end()
        self._points = []
        self.ctx.canvas.mark_layer_dirty()
        self.ctx.canvas.commit_stroke()

    def draw_overlay(self, painter: QPainter):
        if len(self._points) < 1:
            return
        canvas = self.ctx.canvas
        pen = QPen(QColor(120, 170, 255), 1, Qt.DashLine)
        painter.setPen(pen)
        pts = [canvas.doc_to_widget(p) for p in self._points]
        for i in range(len(pts) - 1):
            painter.drawLine(pts[i], pts[i + 1])
