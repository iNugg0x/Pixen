from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor

from app.tools.base_tool import BaseTool


class EyedropperTool(BaseTool):
    name = "eyedropper"
    shortcut = "I"
    cursor = Qt.CrossCursor

    def _pick(self, pos: QPointF, event):
        doc = self.ctx.document
        composited = doc.render()
        x, y = int(pos.x()), int(pos.y())
        if 0 <= x < composited.width() and 0 <= y < composited.height():
            color = QColor(composited.pixel(x, y))
            if event.button() == Qt.RightButton:
                self.ctx.canvas.set_secondary_color(color)
            else:
                self.ctx.canvas.set_primary_color(color)

    def mouse_press(self, pos: QPointF, event):
        self._pick(pos, event)
