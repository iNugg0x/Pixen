"""Settings / shortcuts persistence tests.

QSettings writes to the real OS-native store (registry / plist / config
file) keyed by org+app name "Pixen"/"Pixen", same as the shipped app --
so these also double as a smoke test that settings storage works at all
on the current OS. Every test clears what it wrote so a local test run
doesn't leave junk behind in the real Pixen settings location.
"""
from app.settings.settings_manager import DEFAULTS, SettingsManager
from app.shortcuts.shortcut_manager import DEFAULT_SHORTCUTS, ShortcutManager


def test_settings_defaults_match_declared_types(qapp):
    mgr = SettingsManager()
    mgr.reset_to_defaults()
    for key, default in DEFAULTS.items():
        value = mgr.get(key)
        assert type(value) is type(default), f"{key}: expected {type(default)}, got {type(value)}"
        assert value == default


def test_settings_round_trip(qapp):
    mgr = SettingsManager()
    mgr.set("appearance/theme", "dark")
    mgr.set("canvas/grid_size", 32)
    assert mgr.get("appearance/theme") == "dark"
    assert mgr.get("canvas/grid_size") == 32
    mgr.reset_to_defaults()
    assert mgr.get("appearance/theme") == DEFAULTS["appearance/theme"]


def test_shortcuts_defaults_and_override(qapp):
    mgr = ShortcutManager()
    for action_id in DEFAULT_SHORTCUTS:
        mgr.reset(action_id)
    assert mgr.get("save") == "Ctrl+S"
    mgr.set("save", "Ctrl+Shift+K")
    assert mgr.get("save") == "Ctrl+Shift+K"
    mgr.reset("save")
    assert mgr.get("save") == "Ctrl+S"


def test_shortcut_manager_all_ids_lists_every_default(qapp):
    mgr = ShortcutManager()
    assert set(mgr.all_ids()) == set(DEFAULT_SHORTCUTS.keys())
