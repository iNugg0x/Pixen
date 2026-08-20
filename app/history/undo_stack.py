"""Undo/redo history.

Snapshots are stored as PNG-compressed bytes (not raw QImage buffers) to
keep memory usage reasonable even for large canvases, and the stack depth
is capped. Each snapshot captures the full document layer stack state
(layer images + order/visibility/opacity) at a point in time -- simple and
robust, at some memory cost vs. per-stroke diffing. Good enough for a
lightweight paint app; can be swapped for tile-based diffing later.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QImage

from app.canvas.document import Document, Layer


@dataclass
class LayerSnapshot:
    png_bytes: bytes
    name: str
    visible: bool
    opacity: float
    locked: bool
    id: str


@dataclass
class DocSnapshot:
    layers: List[LayerSnapshot]
    active_layer_index: int
    width: int
    height: int
    label: str = ""


def _image_to_png(img: QImage) -> bytes:
    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def _png_to_image(data: bytes) -> QImage:
    img = QImage()
    img.loadFromData(data, "PNG")
    return img


class HistoryManager:
    def __init__(self, max_depth: int = 50):
        self.max_depth = max_depth
        self._undo: List[DocSnapshot] = []
        self._redo: List[DocSnapshot] = []

    def clear(self):
        self._undo.clear()
        self._redo.clear()

    @property
    def can_undo(self) -> bool:
        return len(self._undo) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo) > 0

    def snapshot(self, doc: Document, label: str = "") -> DocSnapshot:
        return DocSnapshot(
            layers=[
                LayerSnapshot(_image_to_png(l.image), l.name, l.visible,
                               l.opacity, l.locked, l.id)
                for l in doc.layers
            ],
            active_layer_index=doc.active_layer_index,
            width=doc.width, height=doc.height, label=label,
        )

    def push(self, doc: Document, label: str = ""):
        """Call *before* mutating the document to record the pre-change state."""
        self._undo.append(self.snapshot(doc, label))
        if len(self._undo) > self.max_depth:
            self._undo.pop(0)
        self._redo.clear()

    def _apply(self, doc: Document, snap: DocSnapshot):
        doc.width, doc.height = snap.width, snap.height
        doc.layers = [
            Layer(_png_to_image(ls.png_bytes), ls.name, ls.visible,
                  ls.opacity, ls.locked, ls.id)
            for ls in snap.layers
        ]
        doc.active_layer_index = min(snap.active_layer_index, len(doc.layers) - 1)
        doc.dirty = True

    def undo(self, doc: Document) -> bool:
        if not self.can_undo:
            return False
        self._redo.append(self.snapshot(doc, "redo-point"))
        snap = self._undo.pop()
        self._apply(doc, snap)
        return True

    def redo(self, doc: Document) -> bool:
        if not self.can_redo:
            return False
        self._undo.append(self.snapshot(doc, "undo-point"))
        snap = self._redo.pop()
        self._apply(doc, snap)
        return True
