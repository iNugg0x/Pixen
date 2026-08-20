"""Import / initialization smoke tests.

If any module has a syntax error, a missing dependency, or an import-
time crash, these fail fast and say exactly which module -- instead of
that surfacing later as "the app won't launch" with no context.
"""
import importlib
import pkgutil

import app as pixen_app


def _submodules(package):
    for info in pkgutil.walk_packages(package.__path__, prefix=package.__name__ + "."):
        yield info.name


def test_every_app_submodule_imports():
    failures = []
    for name in _submodules(pixen_app):
        try:
            importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - failure path
            failures.append(f"{name}: {exc!r}")
    assert not failures, "modules failed to import:\n" + "\n".join(failures)


def test_main_module_imports():
    import main  # noqa: F401


def test_version_is_set():
    assert pixen_app.__version__
    assert isinstance(pixen_app.__version__, str)


def test_main_window_constructs(qapp):
    """The main window is the app's real entry point -- build one and
    make sure __init__ doesn't raise (docks, menus, toolbar, tools,
    settings/shortcuts all wire up)."""
    from app.ui.main_window import MainWindow

    window = MainWindow()
    assert window.windowTitle().startswith("Untitled")
    assert window.document.width > 0
    assert window.document.height > 0
    window.close()
