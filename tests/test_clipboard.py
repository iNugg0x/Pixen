"""Clipboard test.

The system clipboard isn't reliably available under Qt's "offscreen"
platform plugin (no real windowing system, so no OS clipboard to talk
to) -- this varies by OS and Qt version rather than being something we
control. Rather than assert something that's actually a property of
the *environment* rather than of Pixen's code, this test verifies the
round-trip when a clipboard is available and skips (with a clear
reason) when it isn't, so a CI run stays honest about what it did and
didn't actually exercise.
"""
import pytest
from PySide6.QtGui import QColor, QImage


def test_image_clipboard_round_trip(qapp):
    clipboard = qapp.clipboard()

    img = QImage(4, 4, QImage.Format_ARGB32_Premultiplied)
    img.fill(QColor(10, 20, 30, 255).rgba())
    clipboard.setImage(img)

    result = clipboard.image()
    if result.isNull():
        pytest.skip("No real system clipboard available in this headless environment")

    assert result.width() == 4
    assert result.height() == 4
    assert QColor(result.pixel(0, 0)) == QColor(10, 20, 30, 255)
