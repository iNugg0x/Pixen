from __future__ import annotations

from PySide6.QtCore import QSettings

DEFAULT_SHORTCUTS = {
    "new": "Ctrl+N",
    "open": "Ctrl+O",
    "save": "Ctrl+S",
    "save_as": "Ctrl+Shift+S",
    "undo": "Ctrl+Z",
    "redo": "Ctrl+Y",
    "copy": "Ctrl+C",
    "paste": "Ctrl+V",
    "cut": "Ctrl+X",
    "select_all": "Ctrl+A",
    "deselect": "Ctrl+D",
    "duplicate": "Ctrl+J",
    "zoom_in": "Ctrl++",
    "zoom_out": "Ctrl+-",
    "zoom_fit": "Ctrl+0",
    "zoom_100": "Ctrl+1",
    "fullscreen": "F11",
    "print": "Ctrl+P",
    "tool_pencil": "P",
    "tool_brush": "B",
    "tool_eraser": "E",
    "tool_text": "T",
    "tool_fill": "G",
    "tool_eyedropper": "I",
}


class ShortcutManager:
    """Persists user-customized shortcuts on top of DEFAULT_SHORTCUTS."""

    def __init__(self):
        self.qs = QSettings("Pixen", "Pixen")
        self._overrides = {}
        self.qs.beginGroup("shortcuts")
        for key in self.qs.childKeys():
            self._overrides[key] = self.qs.value(key)
        self.qs.endGroup()

    def get(self, action_id: str) -> str:
        return self._overrides.get(action_id, DEFAULT_SHORTCUTS.get(action_id, ""))

    def set(self, action_id: str, sequence: str):
        self._overrides[action_id] = sequence
        self.qs.beginGroup("shortcuts")
        self.qs.setValue(action_id, sequence)
        self.qs.endGroup()

    def all_ids(self):
        return list(DEFAULT_SHORTCUTS.keys())

    def reset(self, action_id: str):
        self._overrides.pop(action_id, None)
        self.qs.beginGroup("shortcuts")
        self.qs.remove(action_id)
        self.qs.endGroup()
