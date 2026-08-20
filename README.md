# Pixen

A modern, minimal, local-first paint app in the spirit of the classic
Windows Paint — rebuilt for 2026. Python 3.12 + PySide6/Qt.
No AI, no cloud, no accounts, no telemetry, no bloat.

Philosophy: open → create a canvas → draw. Every feature exists for a
clear reason; this is not trying to become Photoshop.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
python main.py
```

Requirements: Python 3.12+, PySide6, NumPy (used only for the flood-fill
tool's pixel buffer operations). Dependencies are kept intentionally
minimal.

## What's implemented

- **Canvas engine**: layered `QImage` compositing with a cached
  composite (only the layers/region that actually changed are
  re-flattened — panning, zooming, selection drags, and shape previews
  reuse the cached image instead of recompositing on every frame),
  pan/zoom (Ctrl+wheel, space+drag, middle-mouse drag), zoom-to-fit,
  HiDPI-aware rendering, checkerboard transparency display, optional
  grid + snap-to-grid.
- **Tools**: pencil, brush, eraser — with a small real-time smoothing
  engine (quadratic-curve fitting through recent points, adjustable
  None/Low/Medium/High in Settings → Tools) so fast strokes come out as
  continuous curves rather than a faceted polyline, plus a discrete
  brush-size preview ring at the cursor. Also: fill (flood fill with
  tolerance), eyedropper, line (Shift = 45° snap), rectangle, ellipse,
  polygon, rectangular selection (movable), freeform/lasso selection,
  text (inline editable box, committed as pixels on confirm). Shift/Alt
  modifiers constrain shapes (square/circle, draw-from-center).
- **Layers**: add / delete / duplicate / reorder (drag or buttons) /
  rename / show-hide / per-layer opacity.
- **History**: multi-step undo/redo (PNG-compressed snapshots, capped
  depth so memory stays bounded).
- **New Document dialog**: A0–A6, Letter, Legal, Tabloid, portrait/
  landscape, DPI presets (72/96/150/300/600 + custom), units (px/mm/
  cm/in), margin presets (visual guide), transparent-background option,
  live pixel-size preview.
- **Canvas resize** (Image → Resize Canvas), with anchor + optional
  content scaling.
- **Images**: add an image onto the current drawing as a new layer,
  drag & drop images (or open as new document if nothing is open).
- **Files**: PNG / JPG / BMP / WebP open & export; a native `.qpaint`
  project format (a zip of per-layer PNGs + a JSON manifest) that
  preserves layers, opacity, and visibility; recent-files list;
  unsaved-changes confirmation on New/Open/Close; optional autosave.
- **Printing**: native OS print dialog + print preview via Qt's
  `QPrintSupport`.
- **Clipboard**: copy/cut/paste/duplicate for the active selection,
  via the system clipboard.
- **Interface**: minimalist toolbar with hand-drawn vector icons
  (consistent stroke weight, theme-aware color — no emoji-font glyphs),
  color panel (palette + primary/secondary swatches + custom color
  dialog), dockable layers panel, slim status bar (dimensions, DPI,
  cursor position, zoom, selection size, layer count), light/dark/
  system theme, Normal / Compact / Canvas-only interface modes,
  fullscreen (F11).
- **Settings dialog**: appearance, canvas defaults, tool defaults
  (including stroke smoothing), file defaults — persisted via
  `QSettings` (registry on Windows, plist on macOS, config file on
  Linux).
- **Shortcuts**: centralized default keymap (`app/shortcuts`), stored
  overrides via `QSettings`. Main accelerators are already wired to
  menu actions.
- **Pen pressure**: tablet-pressure → stroke-size modulation via
  `QTabletEvent`; mouse/touchpad continue to work identically when no
  tablet is present.
- **Identity & packaging**: app renamed end-to-end to Pixen (window
  title, `QSettings` org/app name, file-dialog labels, executable
  name); generated app icon (`assets/icons/pixen.png` / `.ico`);
  `pyproject.toml` with real project metadata; `Pixen.spec` for
  PyInstaller builds on Windows/macOS/Linux; a Linux `.desktop` entry
  under `packaging/`.

## Roadmap against the full spec

The items below are the parts of the spec that aren't built yet. Rough
effort order, not priority — tell me which block to tackle next.

**Precision & navigation**
- Rulers (horizontal/vertical) and draggable guides — grid + snap
  infrastructure already exists, the ruler widgets and guide objects
  don't yet.
- Snap-to-guides / snap-to-edges / snap-to-center + alignment
  indicators (snap-to-grid already works).
- A simple protractor/measurement tool.

**Selection & transform**
- Selection rotate, and dragging a selection's *pixels* (currently a
  rectangular selection marquee can be repositioned, but it doesn't cut
  and carry the underlying pixels).
- Transform handles for images added to the canvas (move exists via
  drag/drop placement; resize/rotate/keep-aspect handles don't exist
  yet).

**Drawing tools**
- A proper curve/Bézier tool (line/rect/ellipse/polygon exist; curves
  don't).
- Brush textures (current brushes are flat pencil/brush/eraser; no
  texture system yet).
- Rotate/flip canvas (horizontal/vertical flip, arbitrary rotate).

**Project & output**
- Templates (save/load canvas presets) — the New Document dialog
  covers sizes/DPI/units/margins but nothing is saved as a reusable
  template yet.
- Margins actually excluded from/drawn on export & print output (the
  New Document dialog collects a margin value as a visual guide; it
  isn't yet respected by print/export).
- A shortcut-remapping settings page (the manager + default keymap
  exist; there's no UI to change bindings interactively yet).

**Distribution**
- `.icns` for macOS (Pillow can't build this format directly — the PNG
  in `assets/icons/` is ready, see "Building a standalone executable"
  below for the one-command macOS step) and a signed/notarized build.
- A Windows installer (Inno Setup / MSIX) and a Linux AppImage/Flatpak,
  built on top of the PyInstaller output.

None of this affects the "no AI, local-first, no accounts" requirements
— those are fully respected throughout (nothing in the app calls out to
a network service).

**Note on testing**: written and syntax-checked (`py_compile`) in a
sandboxed environment without a display server, GPU, or internet
access, so PySide6 can't be installed here to do a full interactive
runtime test. The code follows standard, well-established PySide6/Qt6
APIs throughout, but please run it locally first and report/file any
runtime issues you hit.

## Project layout

```
pixen/
├── main.py
├── pyproject.toml
├── requirements.txt
├── Pixen.spec              # PyInstaller build spec
├── packaging/
│   └── pixen.desktop        # Linux desktop entry
├── app/
│   ├── ui/          # main window, toolbar, dialogs, panels, status bar
│   ├── canvas/       # Document/Layer model, CanvasWidget, paper sizes
│   ├── tools/        # one module per tool family + ToolManager
│   ├── history/      # undo/redo
│   ├── files/        # open/save (raster formats + native .qpaint)
│   ├── printing/      # QPrintSupport integration
│   ├── settings/      # QSettings-backed preferences
│   └── shortcuts/     # keymap defaults + overrides
└── assets/
    └── icons/         # app icon (pixen.png / pixen.ico)
```

## Building a standalone executable

```bash
pip install pyinstaller
pyinstaller Pixen.spec
```

This produces a folder build (`dist/Pixen/`, or `dist/Pixen.app` on
macOS) rather than a single `--onefile` executable, so startup stays
fast — a onefile build has to unpack itself into a temp directory on
every launch. Flip `exclude_binaries`/wrap in `EXE(..., a.binaries, ...)`
directly in `Pixen.spec` if a single distributable file matters more
than launch speed for your release.

**macOS icon**: Pillow (used by `generate_icon.py`) can produce `.ico`
directly but not `.icns`. On a Mac, generate it once with:

```bash
mkdir pixen.iconset
# populate pixen.iconset/icon_16x16.png, icon_32x32.png, ... from assets/icons/pixen.png
iconutil -c icns pixen.iconset -o assets/icons/pixen.icns
```

`Pixen.spec` picks it up automatically once it exists.

**Linux**: install the `.desktop` file from `packaging/pixen.desktop`
alongside the built binary and `assets/icons/pixen.png` per your
distro's icon theme path (e.g. `/usr/share/applications/` and
`/usr/share/icons/hicolor/512x512/apps/`).
