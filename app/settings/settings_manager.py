from __future__ import annotations

from PySide6.QtCore import QSettings

DEFAULTS = {
    "appearance/theme": "system",          # light | dark | system
    "appearance/accent_color": "#4b8bff",
    "appearance/icon_size": "medium",       # small | medium | large
    "appearance/density": "normal",         # compact | normal
    "appearance/animations": True,
    "appearance/ui_mode": "normal",         # normal | compact | canvas-only
    "canvas/show_grid": False,
    "canvas/show_ruler": True,
    "canvas/snap_to_grid": False,
    "canvas/snap_to_guides": True,
    "canvas/grid_size": 20,
    "tools/default_size": 4,
    "tools/default_opacity": 1.0,
    "tools/pen_pressure": True,
    "tools/stroke_smoothing": "medium",     # none | low | medium | high
    "files/default_format": "png",
    "files/jpg_quality": 92,
    "files/autosave_enabled": True,
    "files/autosave_interval_min": 5,
}


class SettingsManager:
    """Thin wrapper over QSettings with typed defaults. Organization/app
    name determine the OS-native storage location (registry on Windows,
    plist on macOS, config file on Linux) -- no custom file handling
    needed."""

    def __init__(self):
        self.qs = QSettings("Pixen", "Pixen")

    def get(self, key: str):
        default = DEFAULTS.get(key)
        value = self.qs.value(key, default)
        if isinstance(default, bool):
            return str(value).lower() in ("true", "1")
        if isinstance(default, int) and not isinstance(default, bool):
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
        if isinstance(default, float):
            try:
                return float(value)
            except (TypeError, ValueError):
                return default
        return value

    def set(self, key: str, value):
        self.qs.setValue(key, value)

    def reset_to_defaults(self):
        self.qs.clear()
