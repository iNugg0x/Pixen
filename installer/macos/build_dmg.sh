#!/bin/bash
# Build a .dmg from the PyInstaller .app bundle. Run on macOS, after
# `pyinstaller Pixen.spec` has produced dist/Pixen.app.
#
# Usage:
#   installer/macos/build_dmg.sh [output-name-without-extension]
#
# Defaults the output name to Pixen-macOS-<arch>.dmg, where <arch> is
# the arch this script is run on (arm64 on Apple Silicon, x86_64 on
# Intel) -- matching what CI needs for each runner. Pass an explicit
# name to override.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP_PATH="$ROOT_DIR/dist/Pixen.app"
ARCH="$(uname -m)"
OUT_NAME="${1:-Pixen-macOS-${ARCH}}"
OUT_DIR="$ROOT_DIR/dist-installer"
DMG_PATH="$OUT_DIR/${OUT_NAME}.dmg"

if [ ! -d "$APP_PATH" ]; then
    echo "error: $APP_PATH not found -- run 'pyinstaller Pixen.spec' first" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"
rm -f "$DMG_PATH"

STAGING_DIR="$(mktemp -d)"
trap 'rm -rf "$STAGING_DIR"' EXIT

cp -R "$APP_PATH" "$STAGING_DIR/"
# A drag-to-Applications shortcut is the standard macOS install UX.
ln -s /Applications "$STAGING_DIR/Applications"

hdiutil create -volname "Pixen" \
    -srcfolder "$STAGING_DIR" \
    -ov -format UDZO \
    "$DMG_PATH"

echo "Created $DMG_PATH"
