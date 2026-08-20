from __future__ import annotations

from PySide6.QtCore import QPointF, Qt, QRectF
from PySide6.QtGui import QPainter, QFont, QColor
from PySide6.QtWidgets import QTextEdit

from app.tools.base_tool import BaseTool


class TextTool(BaseTool):
    """Click to place an editable text box (a QTextEdit overlaid on the
    canvas widget). The text remains editable while selected; clicking
    elsewhere, pressing Escape, or switching tools commits it as pixels
    onto the active layer."""
    name = "text"
    shortcut = "T"

    font_family = "Segoe UI"
    font_size = 24
    bold = False
    italic = False
    underline = False
    color: QColor | None = None

    def activate(self):
        super().activate()
        self._editor: QTextEdit | None = None
        self._doc_pos: QPointF | None = None

    def deactivate(self):
        self.commit()

    def mouse_press(self, pos: QPointF, event):
        if self._editor is not None:
            self.commit()
            return
        self._doc_pos = pos
        canvas = self.ctx.canvas
        editor = QTextEdit(canvas)
        editor.setStyleSheet(
            "QTextEdit { background: rgba(255,255,255,60); border: 1px dashed #4b8bff; }")
        editor.setFont(self._make_font())
        editor.setFixedSize(int(260 * canvas.zoom), int(120 * canvas.zoom))
        screen_pos = canvas.doc_to_widget(pos)
        editor.move(int(screen_pos.x()), int(screen_pos.y()))
        editor.show()
        editor.setFocus()
        self._editor = editor

    def _make_font(self) -> QFont:
        f = QFont(self.font_family, self.font_size)
        f.setBold(self.bold)
        f.setItalic(self.italic)
        f.setUnderline(self.underline)
        return f

    def commit(self):
        if self._editor is None:
            return
        text = self._editor.toPlainText()
        if text.strip():
            self.ctx.canvas.history.push(self.ctx.document, "text")
            layer = self.ctx.document.active_layer
            painter = QPainter(layer.image)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setFont(self._make_font())
            color = self.color or QColor(self.ctx.primary_color)
            painter.setPen(color)
            rect = QRectF(self._doc_pos.x(), self._doc_pos.y(), 800, 600)
            painter.drawText(rect, Qt.TextWordWrap, text)
            painter.end()
            self.ctx.canvas.mark_layer_dirty()
            self.ctx.canvas.commit_stroke()
        self._editor.deleteLater()
        self._editor = None
        self._doc_pos = None

    def key_press(self, event):
        if event.key() == Qt.Key_Escape:
            if self._editor is not None:
                self._editor.deleteLater()
                self._editor = None
