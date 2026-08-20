# PyInstaller spec for building the Pixen desktop executable.
#
# Usage:
#   pip install pyinstaller
#   pyinstaller Pixen.spec
#
# Output goes to dist/Pixen (a folder build, not --onefile) so startup
# stays fast -- a single-file build unpacks itself into a temp dir on
# every launch, which is a noticeable delay for a "should feel fast"
# app. Switch to onefile=True in the EXE() call below if a single
# distributable file matters more than launch speed for your release.
import sys
from pathlib import Path

block_cipher = None
ROOT = Path(SPECPATH)

if sys.platform == "win32":
    icon_file = str(ROOT / "assets" / "icons" / "pixen.ico")
elif sys.platform == "darwin":
    # .icns can't be generated from Python alone -- build it on macOS with
    # `iconutil -c icns pixen.iconset` from the PNG (see README "Building
    # a standalone executable"). Falls back to no icon if not present yet.
    icns = ROOT / "assets" / "icons" / "pixen.icns"
    icon_file = str(icns) if icns.exists() else None
else:
    icon_file = None  # Linux: icon comes from the .desktop file instead

a = Analysis(
    ["main.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[("assets", "assets")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Pixen",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no console window on Windows/macOS
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Pixen",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Pixen.app",
        icon=icon_file,
        bundle_identifier="app.pixen.paint",
        info_plist={
            "CFBundleName": "Pixen",
            "CFBundleDisplayName": "Pixen",
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
        },
    )
