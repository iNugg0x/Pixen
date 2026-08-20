"""Standard paper sizes (mm, portrait orientation) and unit conversions."""

# width_mm, height_mm
PAPER_SIZES_MM = {
    "A0": (841, 1189),
    "A1": (594, 841),
    "A2": (420, 594),
    "A3": (297, 420),
    "A4": (210, 297),
    "A5": (148, 210),
    "A6": (105, 148),
    "Letter": (215.9, 279.4),
    "Legal": (215.9, 355.6),
    "Tabloid": (279.4, 431.8),
}

DPI_PRESETS = [72, 96, 150, 300, 600]

MM_PER_INCH = 25.4


def mm_to_px(mm: float, dpi: int) -> int:
    return round(mm / MM_PER_INCH * dpi)


def cm_to_px(cm: float, dpi: int) -> int:
    return mm_to_px(cm * 10, dpi)


def inch_to_px(inch: float, dpi: int) -> int:
    return round(inch * dpi)


def px_to_unit(px: float, unit: str, dpi: int) -> float:
    if unit == "px":
        return px
    inches = px / dpi
    if unit == "in":
        return inches
    mm = inches * MM_PER_INCH
    if unit == "mm":
        return mm
    if unit == "cm":
        return mm / 10
    return px


def unit_to_px(value: float, unit: str, dpi: int) -> int:
    if unit == "px":
        return round(value)
    if unit == "in":
        return inch_to_px(value, dpi)
    if unit == "mm":
        return mm_to_px(value, dpi)
    if unit == "cm":
        return cm_to_px(value, dpi)
    return round(value)


def paper_size_px(name: str, dpi: int, landscape: bool = False):
    w_mm, h_mm = PAPER_SIZES_MM[name]
    if landscape:
        w_mm, h_mm = h_mm, w_mm
    return mm_to_px(w_mm, dpi), mm_to_px(h_mm, dpi)
