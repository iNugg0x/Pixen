"""Load/save documents.

Standard formats (PNG/JPG/BMP/WebP) flatten the document to a single
image. The native `.qpaint` format is a zip archive containing one PNG
per layer plus a `document.json` manifest, preserving layers, opacity,
visibility and document metadata (DPI, size).
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from typing import Optional

from PySide6.QtGui import QImage

from app.canvas.document import Document, Layer

NATIVE_EXT = ".qpaint"
RASTER_FORMATS = {".png": "PNG", ".jpg": "JPG", ".jpeg": "JPG", ".bmp": "BMP", ".webp": "WEBP"}


def save_native(document: Document, path: str):
    manifest = {
        "width": document.width,
        "height": document.height,
        "dpi": document.dpi,
        "name": document.name,
        "active_layer_index": document.active_layer_index,
        "layers": [],
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, layer in enumerate(document.layers):
            filename = f"layer_{i:03d}.png"
            from PySide6.QtCore import QBuffer, QIODevice
            buf = QBuffer()
            buf.open(QIODevice.WriteOnly)
            layer.image.save(buf, "PNG")
            zf.writestr(filename, bytes(buf.data()))
            manifest["layers"].append({
                "file": filename, "name": layer.name, "visible": layer.visible,
                "opacity": layer.opacity, "locked": layer.locked, "id": layer.id,
            })
        zf.writestr("document.json", json.dumps(manifest, indent=2))
    document.file_path = path
    document.native_format = True
    document.dirty = False


def load_native(path: str) -> Document:
    with zipfile.ZipFile(path, "r") as zf:
        manifest = json.loads(zf.read("document.json"))
        doc = Document(manifest["width"], manifest["height"], manifest.get("dpi", 96),
                        transparent=True, name=manifest.get("name", "Untitled"))
        doc.layers = []
        for layer_info in manifest["layers"]:
            data = zf.read(layer_info["file"])
            img = QImage()
            img.loadFromData(data, "PNG")
            doc.layers.append(Layer(
                image=img, name=layer_info["name"], visible=layer_info["visible"],
                opacity=layer_info["opacity"], locked=layer_info.get("locked", False),
                id=layer_info.get("id", ""),
            ))
        doc.active_layer_index = min(manifest.get("active_layer_index", 0), len(doc.layers) - 1)
    doc.file_path = path
    doc.native_format = True
    doc.dirty = False
    return doc


def load_raster(path: str) -> Document:
    img = QImage(path)
    if img.isNull():
        raise ValueError(f"Could not load image: {path}")
    from PySide6.QtGui import QImage as _QImage
    doc = Document(img.width(), img.height(), 96, transparent=True,
                    name=Path(path).stem)
    doc.layers = [Layer(image=img.convertToFormat(_QImage.Format_ARGB32_Premultiplied),
                         name="Background")]
    doc.file_path = path
    doc.native_format = False
    doc.dirty = False
    return doc


def save_raster(document: Document, path: str, quality: int = 92):
    ext = Path(path).suffix.lower()
    fmt = RASTER_FORMATS.get(ext, "PNG")
    flat = document.render()
    if fmt == "JPG":
        # JPEG has no alpha channel -- flatten onto white first.
        from PySide6.QtGui import QPainter, QColor
        opaque = QImage(flat.size(), QImage.Format_RGB32)
        opaque.fill(QColor("white"))
        p = QPainter(opaque)
        p.drawImage(0, 0, flat)
        p.end()
        flat = opaque
    flat.save(path, fmt, quality)
    document.file_path = path
    document.native_format = False
    document.dirty = False


def open_document(path: str) -> Document:
    if path.lower().endswith(NATIVE_EXT):
        return load_native(path)
    return load_raster(path)


def save_document(document: Document, path: Optional[str] = None):
    path = path or document.file_path
    if path is None:
        raise ValueError("No path given and document has never been saved.")
    if path.lower().endswith(NATIVE_EXT):
        save_native(document, path)
    else:
        save_raster(document, path)
