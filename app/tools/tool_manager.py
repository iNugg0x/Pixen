from __future__ import annotations

from app.tools.base_tool import ToolContext
from app.tools.freehand import PencilTool, BrushTool, EraserTool
from app.tools.fill import FillTool
from app.tools.eyedropper import EyedropperTool
from app.tools.shapes import LineTool, RectangleTool, EllipseTool, PolygonTool
from app.tools.selection import RectSelectionTool, FreeSelectionTool
from app.tools.text_tool import TextTool


TOOL_CLASSES = [
    PencilTool, BrushTool, EraserTool, FillTool, EyedropperTool,
    LineTool, RectangleTool, EllipseTool, PolygonTool,
    RectSelectionTool, FreeSelectionTool, TextTool,
]


class ToolManager:
    def __init__(self, canvas):
        self.ctx = ToolContext(canvas)
        self.tools = {cls.name: cls(self.ctx) for cls in TOOL_CLASSES}
        self.active_tool = None
        self.set_active("brush")

    def set_active(self, name: str):
        if name not in self.tools:
            return
        if self.active_tool is not None:
            self.active_tool.deactivate()
        self.active_tool = self.tools[name]
        self.active_tool.activate()

    def get(self, name: str):
        return self.tools.get(name)
