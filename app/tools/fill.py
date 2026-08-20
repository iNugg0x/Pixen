from __future__ import annotations

import numpy as np
from collections import deque

from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QImage

from app.tools.base_tool import BaseTool


def _qimage_to_array(img: QImage) -> np.ndarray:
    img = img.convertToFormat(QImage.Format_ARGB32)
    ptr = img.bits()
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape(img.height(), img.width(), 4)
    return arr.copy()


def _array_to_qimage(arr: np.ndarray) -> QImage:
    h, w, _ = arr.shape
    img = QImage(arr.tobytes(), w, h, QImage.Format_ARGB32)
    return img.copy()


class FillTool(BaseTool):
    name = "fill"
    shortcut = "G"
    tolerance = 24  # 0-255-ish color distance threshold

    def mouse_press(self, pos: QPointF, event):
        doc = self.ctx.document
        layer = doc.active_layer
        x, y = int(pos.x()), int(pos.y())
        if not (0 <= x < layer.image.width() and 0 <= y < layer.image.height()):
            return
        self.ctx.canvas.history.push(doc, "fill")

        arr = _qimage_to_array(layer.image)  # H,W,4 as B,G,R,A (Qt native order)
        target = arr[y, x].astype(np.int32)
        fill_color = QColor(self.ctx.primary_color)
        fill_bgra = np.array([fill_color.blue(), fill_color.green(),
                               fill_color.red(), fill_color.alpha()], dtype=np.uint8)

        if np.array_equal(target, fill_bgra.astype(np.int32)):
            return

        h, w, _ = arr.shape
        visited = np.zeros((h, w), dtype=bool)
        tol = self.tolerance
        stack = deque([(x, y)])
        visited[y, x] = True

        diff = np.abs(arr.astype(np.int32) - target).sum(axis=2)
        mask = diff <= tol

        # BFS flood fill constrained to the tolerance mask (fast, contiguous)
        while stack:
            cx, cy = stack.popleft()
            arr[cy, cx] = fill_bgra
            for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                if 0 <= nx < w and 0 <= ny < h and not visited[ny, nx] and mask[ny, nx]:
                    visited[ny, nx] = True
                    stack.append((nx, ny))

        layer.image = _array_to_qimage(arr)
        self.ctx.canvas.mark_layer_dirty()
        self.ctx.canvas.commit_stroke()
