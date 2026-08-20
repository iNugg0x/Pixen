from __future__ import annotations

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QPainterPath

from app.tools.base_tool import BaseTool


# How strongly incoming raw points are pulled toward the running average
# before curve-fitting. Lower = more filtering = smoother but slightly
# "rounder" corners; "none" disables smoothing entirely and draws the
# exact input (best for precise pixel-level work).
SMOOTHING_FACTORS = {
    "none": None,
    "low": 0.7,
    "medium": 0.5,
    "high": 0.3,
}


def _midpoint(a: QPointF, b: QPointF) -> QPointF:
    return QPointF((a.x() + b.x()) / 2, (a.y() + b.y()) / 2)


class _StrokeTool(BaseTool):
    """Shared logic for pencil/brush/eraser.

    Raw mouse/tablet points are jittery and, on a fast diagonal move, can
    be far enough apart that a straight line between them looks like a
    visible "corner" rather than a curve. To keep strokes looking natural
    at any drawing speed this keeps the last couple of (optionally
    smoothed) points and draws each new segment as a quadratic curve
    through their midpoints -- the standard technique real-time paint
    tools use to avoid faceted/segmented-looking strokes -- instead of a
    raw polyline. Only the last 1-2 points are ever buffered, so there's
    no perceptible added latency.
    """

    size = 4
    opacity = 1.0
    hard_edge = False  # pencil = hard edge, brush = antialiased
    erase = False
    smoothing = "medium"  # none | low | medium | high

    def activate(self):
        super().activate()
        self._prev_raw = None    # point before _last_raw
        self._last_raw = None    # most recent raw input point
        self._smoothed = None    # running smoothed point (EMA of raw input)

    def _painter_for_stroke(self) -> QPainter:
        layer = self.ctx.document.active_layer
        painter = QPainter(layer.image)
        painter.setRenderHint(QPainter.Antialiasing, not self.hard_edge)
        if self.erase:
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            color = QColor(0, 0, 0, 0)
        else:
            color = QColor(self.ctx.primary_color)
            color.setAlphaF(self.opacity)
        pen = QPen(color, self.size, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(color)
        return painter

    def _next_smoothed_point(self, raw: QPointF) -> QPointF:
        factor = SMOOTHING_FACTORS.get(self.smoothing)
        if factor is None or self._smoothed is None:
            return QPointF(raw)
        return QPointF(
            self._smoothed.x() + (raw.x() - self._smoothed.x()) * factor,
            self._smoothed.y() + (raw.y() - self._smoothed.y()) * factor,
        )

    def mouse_press(self, pos: QPointF, event):
        self.ctx.canvas.history.push(self.ctx.document, self.name)
        self._prev_raw = None
        self._last_raw = pos
        self._smoothed = QPointF(pos)
        painter = self._painter_for_stroke()
        r = self.size / 2
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(pos, r, r)
        painter.end()
        dirty_rect = QRectF(pos.x() - r, pos.y() - r, r * 2, r * 2)
        self.ctx.canvas.mark_layer_dirty(dirty_rect)

    def mouse_move(self, pos: QPointF, event):
        if self._last_raw is None:
            # Not drawing -- just hovering. Nothing to paint onto the
            # layer, but the brush-size preview ring still needs to
            # follow the cursor.
            self.ctx.canvas.update()
            return
        smoothed = self._next_smoothed_point(pos)
        r = self.size / 2
        painter = self._painter_for_stroke()

        if self.smoothing == "none" or self._prev_raw is None:
            # Not enough history yet for a curve (or smoothing disabled):
            # fall back to a straight segment.
            painter.drawLine(self._smoothed, smoothed)
            dirty_rect = QRectF(self._smoothed, smoothed).normalized()
        else:
            start = _midpoint(self._prev_raw, self._smoothed)
            end = _midpoint(self._smoothed, smoothed)
            path = QPainterPath(start)
            path.quadTo(self._smoothed, end)
            painter.drawPath(path)
            dirty_rect = path.boundingRect()

        painter.end()
        self._prev_raw = self._smoothed
        self._last_raw = pos
        self._smoothed = smoothed
        self.ctx.canvas.mark_layer_dirty(dirty_rect.adjusted(-r, -r, r, r))

    def mouse_release(self, pos: QPointF, event):
        # Close out the trailing bit of curve between the last drawn
        # midpoint and the final point so the stroke doesn't stop short.
        if self._prev_raw is not None and self._smoothed is not None:
            r = self.size / 2
            painter = self._painter_for_stroke()
            start = _midpoint(self._prev_raw, self._smoothed)
            path = QPainterPath(start)
            path.quadTo(self._smoothed, self._smoothed)
            painter.drawPath(path)
            painter.end()
            self.ctx.canvas.mark_layer_dirty(path.boundingRect().adjusted(-r, -r, r, r))
        self._prev_raw = None
        self._last_raw = None
        self._smoothed = None
        self.ctx.canvas.commit_stroke()

    def draw_overlay(self, painter: QPainter):
        """Discrete brush-size ring at the cursor, scaled to the current
        zoom, so the user can see how big a stroke will be before they
        draw it."""
        canvas = self.ctx.canvas
        hover = getattr(canvas, "hover_widget_pos", None)
        if hover is None or self._last_raw is not None:
            return  # hide the static preview while actively drawing
        radius = (self.size / 2) * canvas.zoom
        if radius < 1:
            return
        pen = QPen(QColor(140, 140, 140, 200), 1, Qt.SolidLine)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(hover, radius, radius)


class PencilTool(_StrokeTool):
    name = "pencil"
    shortcut = "P"
    hard_edge = True


class BrushTool(_StrokeTool):
    name = "brush"
    shortcut = "B"
    hard_edge = False


class EraserTool(_StrokeTool):
    name = "eraser"
    shortcut = "E"
    hard_edge = False
    erase = True
