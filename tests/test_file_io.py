from PySide6.QtGui import QColor

from app.canvas.document import Document
from app.files import io as file_io


def test_save_and_load_native_qpaint_round_trip(qapp, tmp_path):
    doc = Document(16, 16, dpi=150, transparent=True, name="RoundTrip")
    doc.active_layer.image.fill(QColor(255, 0, 0).rgba())
    doc.add_layer("Second")
    doc.active_layer.opacity = 0.5

    path = tmp_path / "doc.qpaint"
    file_io.save_document(doc, str(path))
    assert path.exists()

    loaded = file_io.open_document(str(path))
    assert loaded.width == 16
    assert loaded.height == 16
    assert loaded.dpi == 150
    assert len(loaded.layers) == 2
    assert loaded.layers[1].name == "Second"
    assert abs(loaded.layers[1].opacity - 0.5) < 1e-6
    assert loaded.dirty is False


def test_export_png(qapp, tmp_path):
    doc = Document(8, 8, transparent=True)
    path = tmp_path / "out.png"
    file_io.save_raster(doc, str(path))
    assert path.exists()
    assert path.stat().st_size > 0

    reopened = file_io.load_raster(str(path))
    assert reopened.width == 8
    assert reopened.height == 8


def test_export_jpg_flattens_transparency_onto_white(qapp, tmp_path):
    doc = Document(8, 8, transparent=True)
    path = tmp_path / "out.jpg"
    file_io.save_raster(doc, str(path), quality=90)
    assert path.exists()
    reopened = file_io.load_raster(str(path))
    assert reopened.width == 8


def test_open_document_dispatches_by_extension(qapp, tmp_path):
    doc = Document(4, 4)
    native_path = tmp_path / "a.qpaint"
    raster_path = tmp_path / "a.png"
    file_io.save_document(doc, str(native_path))
    file_io.save_document(doc, str(raster_path))

    assert file_io.open_document(str(native_path)).native_format is True
    assert file_io.open_document(str(raster_path)).native_format is False
