from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog

from app.canvas.document import Document


def _render_to_printer(document: Document, printer: QPrinter):
    image = document.render()
    painter = QPainter(printer)
    page_rect = printer.pageRect(QPrinter.DevicePixel)
    scaled = image.scaled(int(page_rect.width()), int(page_rect.height()),
                           Qt.KeepAspectRatio, Qt.SmoothTransformation)
    x = page_rect.x() + (page_rect.width() - scaled.width()) / 2
    y = page_rect.y() + (page_rect.height() - scaled.height()) / 2
    painter.drawImage(QRectF(x, y, scaled.width(), scaled.height()), scaled)
    painter.end()


def print_document(document: Document, parent=None) -> bool:
    printer = QPrinter(QPrinter.HighResolution)
    printer.setResolution(document.dpi or 300)
    printer.setOrientation(QPrinter.Landscape if document.width > document.height
                            else QPrinter.Portrait)
    dialog = QPrintDialog(printer, parent)
    if dialog.exec() != QPrintDialog.Accepted:
        return False
    _render_to_printer(document, printer)
    return True


def preview_document(document: Document, parent=None):
    printer = QPrinter(QPrinter.HighResolution)
    printer.setResolution(document.dpi or 300)
    dialog = QPrintPreviewDialog(printer, parent)
    dialog.paintRequested.connect(lambda p: _render_to_printer(document, p))
    dialog.exec()
