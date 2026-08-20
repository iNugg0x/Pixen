# Pixen

A modern, minimal, local-first paint app in the spirit of the classic
Windows Paint — rebuilt for 2026. Python 3.12 + PySide6/Qt. Runs
natively on Windows, Linux, and macOS (Intel + Apple Silicon) from one
codebase. No AI, no cloud, no accounts, no telemetry, no bloat.

Philosophy: open → create a canvas → draw. Every feature exists for a
clear reason; this is not trying to become Photoshop.

## Download

Pre-built, no-Python-required downloads are published on the
[**GitHub Releases**](../../releases) page of this repository for
every tagged version:

| Platform | File |
|---|---|
| Windows x64 (installer) | `Pixen-Setup.exe` |
| Windows x64 (portable, no install) | `Pixen-Windows-x64-Portable.zip` |
| Linux x86_64 | `Pixen-Linux-x86_64.AppImage` |
| macOS — Apple Silicon | `Pixen-macOS-arm64.dmg` |

(No pre-built Intel macOS `.dmg` — see "Building & releasing" below.)

Go to **[Releases → latest](../../releases/latest)** and download the
file for your system. No other download source is official.

## Quick start (running from source)

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
- **Cross-platform storage**: settings via `QSettings` (registry on
  Windows, plist on macOS, config file on Linux); autosave and any
  other per-user app data via `QStandardPaths` (`app/paths.py`) —
  never inside the install folder, so it works without admin/root.
- **Distribution**: single-source `__version__` (`app/__init__.py`)
  driving the app, `pyproject.toml`, and packaged builds; Windows
  installer (Inno Setup) + portable ZIP; Linux AppImage; macOS DMGs
  for both Apple Silicon and Intel, with `.icns` generated on the fly;
  GitHub Actions builds all four on every version tag and publishes
  them directly to this repo's Releases — see "Building &
  releasing" below.

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
- Code signing / notarization for the macOS DMGs and a signed Windows
  installer (neither is set up — unsigned builds will show an
  OS "unknown publisher" warning on first launch; this needs a paid
  certificate you'd provide as a repo secret, out of scope here).
- `.deb` / `.rpm` packages for Linux (the AppImage covers all major
  distros already; see spec section 20).

None of this affects the "no AI, local-first, no accounts" requirements
— those are fully respected throughout (nothing in the app calls out to
a network service).

**Note on testing**: this was written and verified in a sandboxed
environment with no network access, so `pip install PySide6` (and
therefore an actual interactive run of the app, or of the `tests/`
suite) was not possible here — only `python -m compileall` (syntax/
import-structure checking of every file) and manual code review. The
GitHub Actions CI workflow (`.github/workflows/ci.yml`) runs the real
test suite headlessly on Windows, Linux, and both macOS architectures
on every push, and the release workflow does full PyInstaller builds
on all four targets — but until those have actually run on GitHub (or
you've run the app locally), nothing here should be taken as
"confirmed working," only "should work, following standard PySide6/Qt6
APIs throughout." Please push to a branch, let CI run, and try a local
`python main.py` before trusting a release build.

## Project layout

```
pixen/
├── main.py
├── pyproject.toml
├── requirements.txt
├── Pixen.spec                  # PyInstaller build spec (all 3 OSes)
├── LICENSE
├── packaging/
│   └── pixen.desktop            # Linux desktop entry
├── installer/
│   ├── windows/pixen.iss         # Inno Setup script → Pixen-Setup.exe
│   ├── macos/
│   │   ├── make_icns.sh           # PNG → .icns (must run on macOS)
│   │   └── build_dmg.sh           # .app → .dmg
│   └── linux/build_appimage.sh    # PyInstaller output → .AppImage
├── .github/workflows/
│   ├── ci.yml                    # sanity build + tests, every push/PR
│   └── release.yml                # tag push → build all 4 → GitHub Release
├── tests/                        # pytest suite (see "Testing" below)
├── app/
│   ├── ui/          # main window, toolbar, dialogs, panels, status bar
│   ├── canvas/       # Document/Layer model, CanvasWidget, paper sizes
│   ├── tools/        # one module per tool family + ToolManager
│   ├── history/      # undo/redo
│   ├── files/        # open/save (raster formats + native .qpaint)
│   ├── printing/      # QPrintSupport integration
│   ├── settings/      # QSettings-backed preferences
│   ├── shortcuts/     # keymap defaults + overrides
│   └── paths.py        # asset resolution + per-OS data dir (QStandardPaths)
└── assets/
    └── icons/         # app icon (pixen.png / pixen.ico / pixen.icns once built)
```

## Testing

```bash
pip install -r requirements.txt pytest
python -m pytest
```

The suite (`tests/`) covers: every module imports cleanly, the main
window constructs, document creation/layers/resize, native `.qpaint`
and raster (PNG/JPG) open+save round-trips, `QSettings`/shortcuts
persistence and reset, asset-path resolution, the per-OS data
directory, clipboard image round-trip (skips itself gracefully if the
headless environment has no real system clipboard), and that
`requirements.txt` and `pyproject.toml` agree on dependencies. It
needs `QT_QPA_PLATFORM=offscreen` to run without a display (`tests/conftest.py`
sets this automatically if it isn't already set).

## Building a standalone executable locally

```bash
pip install pyinstaller
pyinstaller Pixen.spec
```

This produces a folder build (`dist/Pixen/`, or `dist/Pixen.app` on
macOS) rather than a single `--onefile` executable, so startup stays
fast — a onefile build has to unpack itself into a temp directory on
every launch.

From there, build the platform-specific package:

**Windows** — installer + portable zip:
```powershell
Compress-Archive -Path dist\Pixen -DestinationPath dist-installer\Pixen-Windows-x64-Portable.zip
# Requires Inno Setup (https://jrsoftware.org/isinfo.php) installed:
iscc installer\windows\pixen.iss /DPixenVersion=1.0.0
```
Produces `dist-installer\Pixen-Setup.exe` (lets the user pick install
location, adds a Start Menu shortcut, uninstalls cleanly — no admin
rights required, per-user install) and the portable zip.

**Linux** — AppImage:
```bash
bash installer/linux/build_appimage.sh
```
Downloads `appimagetool` on first run (cached under
`installer/linux/tools/`) and produces
`dist-installer/Pixen-Linux-x86_64.AppImage`. No Python or install
step needed on the target machine; works across Ubuntu, Debian, Mint,
Fedora, Arch, Manjaro, openSUSE, Pop!_OS, etc.

**macOS** — DMG (must run on an actual Mac; produces a DMG for
whichever architecture you run it on):
```bash
bash installer/macos/make_icns.sh   # once, or whenever the icon changes
pyinstaller Pixen.spec
bash installer/macos/build_dmg.sh
```
Produces `dist-installer/Pixen-macOS-arm64.dmg` (Apple Silicon) or
`Pixen-macOS-x86_64.dmg` (Intel), matching the Mac you built it on.

Install the Linux `.desktop` file (`packaging/pixen.desktop`) manually
only if you're not using the AppImage — e.g. for a `.deb`/`.rpm`,
alongside `assets/icons/pixen.png` per your distro's icon theme path.

## Releasing (GitHub Actions → GitHub Releases)

Everything above also runs automatically in CI. The whole release
process is:

```bash
git push origin main
git tag v1.0.0
git push origin v1.0.0
```

Pushing a `vX.Y.Z` tag triggers `.github/workflows/release.yml`, which:

1. Reads the version from the tag and writes it into `app/__init__.py`
   (the single source of truth main.py, the About dialog, and
   `Pixen.spec`'s macOS bundle version all read from) on each runner.
2. Builds Windows (`windows-latest`), Linux (`ubuntu-latest`), and
   macOS Apple Silicon (`macos-14`) in parallel, using the official
   GitHub-hosted runners for each OS — you don't need to own a Mac or
   a Linux box. (Intel macOS is deliberately not built in CI — GitHub's
   hosted `macos-13` Intel runners have had multi-hour queue times; see
   the comment at the top of `release.yml`. Build that `.dmg` locally
   per the macOS instructions above if you need one.)
3. Collects the four output files and publishes them directly to a new
   **GitHub Release** for that tag (`softprops/action-gh-release`,
   using the automatic `secrets.GITHUB_TOKEN` — no manual token setup,
   no manual upload) with basic auto-generated release notes.

Users then find the download on this repo's
[**Releases**](../../releases) page — nothing is left sitting only as
a GitHub Actions "Artifact" (those aren't linked from anywhere users
would look, and expire after 90 days by default). Required repo
setting: none beyond default — the workflow's `permissions: contents:
write` is enough for `GITHUB_TOKEN` to create the Release.
