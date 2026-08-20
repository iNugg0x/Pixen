"""Core data model: Layer and Document.

A Document owns an ordered list of Layers. Each Layer wraps a QImage
(ARGB32_Premultiplied) plus metadata (name, visibility, opacity).
Compositing is done on demand by Document.render().
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from PySide6.QtCore import QRect, QRectF, QSize
from PySide6.QtGui import QImage, QPainter, QColor


def new_transparent_image(size: QSize) -> QImage:
    img = QImage(size, QImage.Format_ARGB32_Premultiplied)
    img.fill(0)
    return img


@dataclass
class Layer:
    image: QImage
    name: str = "Layer"
    visible: bool = True
    opacity: float = 1.0
    locked: bool = False
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    def clone(self) -> "Layer":
        return Layer(
            image=self.image.copy(),
            name=self.name,
            visible=self.visible,
            opacity=self.opacity,
            locked=self.locked,
            id=self.id,
        )


class Document:
    """Owns layers + canvas metadata (size, dpi, background)."""

    def __init__(self, width: int, height: int, dpi: int = 96,
                 transparent: bool = False, name: str = "Untitled"):
        self.width = width
        self.height = height
        self.dpi = dpi
        self.name = name
        self.file_path: Optional[str] = None
        self.native_format = False  # True if saved as .qpaint project
        self.layers: List[Layer] = []
        self.active_layer_index = 0
        self.dirty = False  # unsaved-changes flag (title bar / save prompts)

        # Cached composite of all layers, rebuilt on demand. Kept separate
        # from `dirty` above since that flag tracks *save* state, not
        # render-cache validity -- conflating them would clear the
        # unsaved-changes indicator every time the canvas repaints.
        self._composite: Optional[QImage] = None
        self._composite_stale = True

        base = new_transparent_image(QSize(width, height))
        if not transparent:
            base.fill(QColor("white").rgb() | 0xFF000000)
        self.layers.append(Layer(image=base, name="Background"))

    # -- layer helpers -----------------------------------------------
    @property
    def active_layer(self) -> Layer:
        return self.layers[self.active_layer_index]

    def add_layer(self, name: Optional[str] = None, above_active: bool = True) -> Layer:
        img = new_transparent_image(QSize(self.width, self.height))
        layer = Layer(image=img, name=name or f"Layer {len(self.layers) + 1}")
        idx = self.active_layer_index + 1 if above_active else len(self.layers)
        self.layers.insert(idx, layer)
        self.active_layer_index = idx
        self.dirty = True
        self._composite_stale = True
        return layer

    def duplicate_layer(self, index: Optional[int] = None) -> Layer:
        index = self.active_layer_index if index is None else index
        clone = self.layers[index].clone()
        clone.id = uuid.uuid4().hex[:8]
        clone.name = f"{clone.name} copy"
        self.layers.insert(index + 1, clone)
        self.active_layer_index = index + 1
        self.dirty = True
        self._composite_stale = True
        return clone

    def remove_layer(self, index: Optional[int] = None):
        if len(self.layers) <= 1:
            return
        index = self.active_layer_index if index is None else index
        del self.layers[index]
        self.active_layer_index = max(0, min(self.active_layer_index, len(self.layers) - 1))
        self.dirty = True
        self._composite_stale = True

    def move_layer(self, from_index: int, to_index: int):
        if 0 <= from_index < len(self.layers) and 0 <= to_index < len(self.layers):
            layer = self.layers.pop(from_index)
            self.layers.insert(to_index, layer)
            self.active_layer_index = to_index
            self.dirty = True
            self._composite_stale = True

    def invalidate(self):
        """Force a full composite rebuild on the next render() call. Call
        this after any change made directly to a layer's pixels/visibility/
        opacity that isn't routed through composite_region()."""
        self._composite_stale = True

    # -- compositing ---------------------------------------------------
    def render(self, only_visible: bool = True) -> QImage:
        """Return the composited image, rebuilding it only if something
        has changed since the last call. Most repaints (panning, zooming,
        selection/shape-preview drags, cursor moves) don't touch layer
        pixels at all, so they now just reuse the cached image instead of
        re-flattening every layer on every frame."""
        if self._composite is None or self._composite_stale:
            self._composite = self._composite_full(only_visible)
            self._composite_stale = False
        return self._composite

    def _composite_full(self, only_visible: bool = True) -> QImage:
        result = new_transparent_image(QSize(self.width, self.height))
        painter = QPainter(result)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        for layer in self.layers:
            if only_visible and not layer.visible:
                continue
            painter.setOpacity(layer.opacity)
            painter.drawImage(0, 0, layer.image)
        painter.end()
        return result

    def composite_region(self, rect: QRect, only_visible: bool = True) -> QImage:
        """Patch just `rect` of the cached composite instead of re-
        flattening the whole document. Used for incremental stroke edits
        (pencil/brush/eraser) so drawing on a big multi-layer canvas stays
        smooth -- cost scales with the size of the stroke, not the size
        of the document."""
        if self._composite is None or self._composite_stale:
            return self.render(only_visible)
        rect = rect.intersected(QRect(0, 0, self.width, self.height))
        if rect.isEmpty():
            return self._composite
        painter = QPainter(self._composite)
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.fillRect(rect, QColor(0, 0, 0, 0))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.setClipRect(rect)
        for layer in self.layers:
            if only_visible and not layer.visible:
                continue
            painter.setOpacity(layer.opacity)
            painter.drawImage(0, 0, layer.image)
        painter.end()
        return self._composite

    def resize_canvas(self, new_width: int, new_height: int,
                       anchor: str = "center", resize_content: bool = False):
        """Resize the canvas. If resize_content is False, content stays at
        its original pixel size and is repositioned per `anchor`; otherwise
        it is scaled to fit the new dimensions."""
        dx, dy = self._anchor_offset(anchor, self.width, self.height, new_width, new_height)
        for layer in self.layers:
            new_img = new_transparent_image(QSize(new_width, new_height))
            painter = QPainter(new_img)
            if resize_content:
                painter.drawImage(QRect(0, 0, new_width, new_height), layer.image)
            else:
                painter.drawImage(dx, dy, layer.image)
            painter.end()
            layer.image = new_img
        self.width, self.height = new_width, new_height
        self.dirty = True
        self._composite_stale = True

    @staticmethod
    def _anchor_offset(anchor: str, ow: int, oh: int, nw: int, nh: int):
        positions = {
            "top-left": (0, 0), "top": ((nw - ow) // 2, 0), "top-right": (nw - ow, 0),
            "left": (0, (nh - oh) // 2), "center": ((nw - ow) // 2, (nh - oh) // 2),
            "right": (nw - ow, (nh - oh) // 2),
            "bottom-left": (0, nh - oh), "bottom": ((nw - ow) // 2, nh - oh),
            "bottom-right": (nw - ow, nh - oh),
        }
        return positions.get(anchor, positions["center"])
