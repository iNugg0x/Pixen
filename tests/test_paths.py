from app.paths import app_root, asset_path, autosave_dir, user_data_dir


def test_asset_path_finds_bundled_icons():
    png = asset_path("icons", "pixen.png")
    ico = asset_path("icons", "pixen.ico")
    assert png.exists(), f"expected {png} to exist"
    assert ico.exists(), f"expected {ico} to exist"


def test_app_root_is_the_project_root_when_run_from_source():
    root = app_root()
    assert (root / "main.py").exists()
    assert (root / "assets").is_dir()


def test_user_data_dir_is_writable(qapp):
    path = user_data_dir()
    assert path.exists()
    probe = path / ".pixen_write_test"
    probe.write_text("ok")
    assert probe.read_text() == "ok"
    probe.unlink()


def test_autosave_dir_is_created_under_user_data_dir(qapp):
    path = autosave_dir()
    assert path.exists()
    assert path.parent == user_data_dir()
