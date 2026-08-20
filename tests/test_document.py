from app.canvas.document import Document


def test_document_creation_default_layer(qapp):
    doc = Document(64, 48, dpi=96, transparent=True, name="Test")
    assert doc.width == 64
    assert doc.height == 48
    assert len(doc.layers) == 1
    assert doc.active_layer.name == "Background"


def test_add_remove_duplicate_layer(qapp):
    doc = Document(32, 32)
    doc.add_layer()
    assert len(doc.layers) == 2
    assert doc.active_layer_index == 1

    doc.duplicate_layer()
    assert len(doc.layers) == 3

    doc.remove_layer()
    assert len(doc.layers) == 2

    # Removing down to the last layer is a no-op -- a document must
    # always have at least one layer.
    doc.remove_layer()
    doc.remove_layer()
    assert len(doc.layers) == 1


def test_move_layer(qapp):
    doc = Document(32, 32)
    doc.add_layer()
    doc.add_layer()
    names = [l.id for l in doc.layers]
    doc.move_layer(0, 2)
    assert [l.id for l in doc.layers] == [names[1], names[2], names[0]]


def test_render_produces_correctly_sized_image(qapp):
    doc = Document(40, 30)
    img = doc.render()
    assert img.width() == 40
    assert img.height() == 30


def test_resize_canvas(qapp):
    doc = Document(20, 20)
    doc.resize_canvas(40, 40, anchor="center", resize_content=False)
    assert doc.width == 40
    assert doc.height == 40
    for layer in doc.layers:
        assert layer.image.width() == 40
        assert layer.image.height() == 40
