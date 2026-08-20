"""Base class every drawing tool implements. The canvas widget forwards
raw mouse/tablet events to the active tool; tools paint directly onto the
active layer's QImage via QPainter."""
from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QCursor


class ToolContext:
    """Shared state tools read from (color, sizes, canvas widget, etc.)."""

    def __init__(self, canvas):
        self.canvas = canvas  # CanvasWidget

    @property
    def document(self):
        return self.canvas.document

    @property
    def primary_color(self):
        return self.canvas.primary_color

    @property
    def secondary_color(self):
        return self.canvas.secondary_color


class BaseTool:
    name = "base"
    shortcut = None
    cursor = Qt.CrossCursor

    def __init__(self, ctx: ToolContext):
        self.ctx = ctx
        self.active = False

    # Lifecycle -----------------------------------------------------
    def activate(self):
        self.ctx.canvas.setCursor(QCursor(self.cursor))

    def deactivate(self):
        pass

    # Events (pos is in image/document pixel coordinates, QPointF) --
    def mouse_press(self, pos: QPointF, event):
        pass

    def mouse_move(self, pos: QPointF, event):
        pass

    def mouse_release(self, pos: QPointF, event):
        pass

    def draw_overlay(self, painter: QPainter):
        """Optional overlay drawn in widget (screen) space, e.g. shape preview."""
        pass

    def key_press(self, event):
        pass
