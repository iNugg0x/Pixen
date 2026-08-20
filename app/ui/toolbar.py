from __future__ import annotations

import math

from PySide6.QtCore import Qt, QSize, QPointF, QRectF
from PySide6.QtGui import (QAction, QActionGroup, QIcon, QPixmap, QPainter,
                            QColor, QPen, QPainterPath)
from PySide6.QtWidgets import QToolBar, QSpinBox, QLabel, QSlider


# Tools shown directly in the main toolbar (the "easily accessible" set).
PRIMARY_TOOLS = [
    ("pencil", "Pencil (P)", "P"),
    ("brush", "Brush (B)", "B"),
    ("eraser", "Eraser (E)", "E"),
    ("fill", "Fill (G)", "G"),
    ("eyedropper", "Eyedropper (I)", "I"),
    ("select-rect", "Rectangle select", "S"),
    ("select-free", "Freeform select", "L"),
    ("line", "Line", "N"),
    ("rectangle", "Rectangle", "R"),
    ("ellipse", "Ellipse", "O"),
    ("polygon", "Polygon", "Y"),
    ("text", "Text (T)", "T"),
]

# Fallback colors matched to the app's light/dark QSS in main_window.py,
# used if the current QPalette can't be read for some reason.
ICON_COLOR_LIGHT = "#3a3a3a"
ICON_COLOR_DARK = "#e6e6e6"

_ICON_SIZE = 26
_STROKE = 1.8


def _new_painter(pm: QPixmap, color: QColor) -> QPainter:
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing, True)
    pen = QPen(color, _STROKE, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.NoBrush)
    return p


def _draw_pencil(p: QPainter, c: QColor):
    p.save()
    p.translate(_ICON_SIZE / 2, _ICON_SIZE / 2)
    p.rotate(45)
    p.drawRoundedRect(QRectF(-3, -10, 6, 15), 1.5, 1.5)
    tip = QPainterPath()
    tip.moveTo(-3, 5)
    tip.lineTo(3, 5)
    tip.lineTo(0, 11)
    tip.closeSubpath()
    p.setBrush(c)
    p.drawPath(tip)
    p.restore()


def _draw_brush(p: QPainter, c: QColor):
    p.save()
    p.translate(_ICON_SIZE / 2, _ICON_SIZE / 2)
    p.rotate(45)
    p.drawLine(QPointF(0, -11), QPointF(0, -2))
    head = QPainterPath()
    head.moveTo(-3.2, -2)
    head.quadTo(-3.2, 6, 0, 11)
    head.quadTo(3.2, 6, 3.2, -2)
    head.closeSubpath()
    p.setBrush(c)
    p.drawPath(head)
    p.restore()


def _draw_eraser(p: QPainter, c: QColor):
    p.save()
    p.translate(_ICON_SIZE / 2, _ICON_SIZE / 2)
    p.rotate(-30)
    p.drawPath(_rounded_rect_path(QRectF(-7, -5, 14, 10), 2))
    p.drawLine(QPointF(-7, 0), QPointF(7, 0))
    p.restore()


def _rounded_rect_path(rect: QRectF, radius: float) -> QPainterPath:
    path = QPainterPath()
    path.addRoundedRect(rect, radius, radius)
    return path


def _draw_fill(p: QPainter, c: QColor):
    p.save()
    p.translate(_ICON_SIZE / 2, _ICON_SIZE / 2 - 1)
    p.rotate(-20)
    bucket = QPainterPath()
    bucket.moveTo(-6, -3)
    bucket.lineTo(6, -3)
    bucket.lineTo(4, 6)
    bucket.lineTo(-4, 6)
    bucket.closeSubpath()
    p.drawPath(bucket)
    p.drawLine(QPointF(-6, -3), QPointF(6, -3))
    p.restore()
    p.setBrush(c)
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(_ICON_SIZE / 2 + 6, _ICON_SIZE / 2 + 6), 1.6, 1.6)


def _draw_eyedropper(p: QPainter, c: QColor):
    p.save()
    p.translate(_ICON_SIZE / 2, _ICON_SIZE / 2)
    p.rotate(45)
    p.drawLine(QPointF(0, -10), QPointF(0, 6))
    p.drawRoundedRect(QRectF(-3, -11, 6, 5), 2, 2)
    tip = QPainterPath()
    tip.moveTo(-2, 6)
    tip.lineTo(2, 6)
    tip.lineTo(0, 10)
    tip.closeSubpath()
    p.setBrush(c)
    p.drawPath(tip)
    p.restore()


def _draw_select_rect(p: QPainter, c: QColor):
    pen = p.pen()
    pen.setStyle(Qt.DashLine)
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    p.drawRect(QRectF(_ICON_SIZE / 2 - 8, _ICON_SIZE / 2 - 6, 16, 12))


def _draw_select_free(p: QPainter, c: QColor):
    pen = p.pen()
    pen.setStyle(Qt.DashLine)
    pen.setDashPattern([2, 2])
    p.setPen(pen)
    path = QPainterPath()
    cx, cy = _ICON_SIZE / 2, _ICON_SIZE / 2
    path.moveTo(cx - 7, cy - 1)
    path.cubicTo(cx - 8, cy - 8, cx + 2, cy - 9, cx + 7, cy - 4)
    path.cubicTo(cx + 10, cy - 1, cx + 6, cy + 6, cx, cy + 6)
    path.cubicTo(cx - 6, cy + 6, cx - 8, cy + 3, cx - 7, cy - 1)
    p.drawPath(path)


def _draw_line(p: QPainter, c: QColor):
    p.drawLine(QPointF(_ICON_SIZE / 2 - 8, _ICON_SIZE / 2 + 8),
               QPointF(_ICON_SIZE / 2 + 8, _ICON_SIZE / 2 - 8))


def _draw_rectangle(p: QPainter, c: QColor):
    p.drawRoundedRect(QRectF(_ICON_SIZE / 2 - 8, _ICON_SIZE / 2 - 6, 16, 12), 1.5, 1.5)


def _draw_ellipse(p: QPainter, c: QColor):
    p.drawEllipse(QPointF(_ICON_SIZE / 2, _ICON_SIZE / 2), 8, 6)


def _draw_polygon(p: QPainter, c: QColor):
    cx, cy, r = _ICON_SIZE / 2, _ICON_SIZE / 2, 8
    path = QPainterPath()
    for i in range(5):
        angle = math.radians(-90 + i * 72)
        pt = QPointF(cx + r * math.cos(angle), cy + r * math.sin(angle))
        if i == 0:
            path.moveTo(pt)
        else:
            path.lineTo(pt)
    path.closeSubpath()
    p.drawPath(path)


def _draw_text(p: QPainter, c: QColor):
    cx, cy = _ICON_SIZE / 2, _ICON_SIZE / 2
    p.drawLine(QPointF(cx - 6, cy - 7), QPointF(cx + 6, cy - 7))
    p.drawLine(QPointF(cx, cy - 7), QPointF(cx, cy + 7))
    p.drawLine(QPointF(cx - 3, cy + 7), QPointF(cx + 3, cy + 7))


_ICON_DRAWERS = {
    "pencil": _draw_pencil,
    "brush": _draw_brush,
    "eraser": _draw_eraser,
    "fill": _draw_fill,
    "eyedropper": _draw_eyedropper,
    "select-rect": _draw_select_rect,
    "select-free": _draw_select_free,
    "line": _draw_line,
    "rectangle": _draw_rectangle,
    "ellipse": _draw_ellipse,
    "polygon": _draw_polygon,
    "text": _draw_text,
}


def _make_icon(name: str, color: str) -> QIcon:
    """Small, hand-drawn vector icon: one consistent stroke weight and a
    single flat color, so it stays crisp at toolbar size and adapts
    cleanly to light/dark themes.

    Deliberately not built from emoji-font glyphs (the old approach):
    those render as multi-color bitmaps on most platforms/fonts and
    ignore the QPainter pen color entirely, plus glyph coverage/alignment
    varies a lot across systems -- that's what made the old toolbar look
    inconsistent."""
    pm = QPixmap(_ICON_SIZE, _ICON_SIZE)
    qc = QColor(color)
    painter = _new_painter(pm, qc)
    drawer = _ICON_DRAWERS.get(name)
    if drawer:
        drawer(painter, qc)
    painter.end()
    return QIcon(pm)


def _current_icon_color() -> str:
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is not None:
        text_color = app.palette().windowText().color()
        if text_color.isValid():
            return text_color.name()
    return ICON_COLOR_LIGHT


def build_toolbar(window) -> QToolBar:
    """window must expose: .tool_manager, .set_active_tool(name),
    .canvas (CanvasWidget)"""
    bar = QToolBar("Tools", window)
    bar.setMovable(False)
    bar.setIconSize(QSize(_ICON_SIZE, _ICON_SIZE))
    bar.setObjectName("mainToolBar")

    group = QActionGroup(window)
    group.setExclusive(True)
    window.tool_actions = {}

    color = _current_icon_color()
    for name, tooltip, shortcut in PRIMARY_TOOLS:
        icon = _make_icon(name, color)
        action = QAction(icon, tooltip, window)
        action.setCheckable(True)
        action.setShortcut(shortcut)
        action.triggered.connect(lambda checked, n=name: window.set_active_tool(n))
        group.addAction(action)
        bar.addAction(action)
        window.tool_actions[name] = action

    window.tool_actions["brush"].setChecked(True)

    bar.addSeparator()

    size_label = QLabel(" Size ")
    bar.addWidget(size_label)
    size_spin = QSpinBox()
    size_spin.setRange(1, 200)
    size_spin.setValue(4)
    size_spin.valueChanged.connect(window.set_tool_size)
    bar.addWidget(size_spin)
    window.size_spin = size_spin

    bar.addWidget(QLabel(" Opacity "))
    opacity_slider = QSlider(Qt.Horizontal)
    opacity_slider.setFixedWidth(90)
    opacity_slider.setRange(1, 100)
    opacity_slider.setValue(100)
    opacity_slider.valueChanged.connect(window.set_tool_opacity)
    bar.addWidget(opacity_slider)
    window.opacity_slider = opacity_slider

    return bar


def refresh_toolbar_icons(window, color: str = None):
    """Re-draw the tool icons in the given (or theme-appropriate) color.
    Call after switching light/dark theme so icons don't end up grey-on-
    grey or otherwise low-contrast against the new toolbar background."""
    color = color or _current_icon_color()
    for name, action in getattr(window, "tool_actions", {}).items():
        action.setIcon(_make_icon(name, color))
