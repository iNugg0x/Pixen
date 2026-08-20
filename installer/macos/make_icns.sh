#!/bin/bash
# Generate assets/icons/pixen.icns from assets/icons/pixen.png.
# Must run on macOS (uses the built-in `iconutil`, which has no
# cross-platform equivalent -- this is the one truly macOS-only step
# in the whole build pipeline). Pixen.spec picks up the .icns
# automatically once it exists; if it's missing, the macOS build just
# falls back to no custom icon instead of failing.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SRC_PNG="$ROOT_DIR/assets/icons/pixen.png"
ICONSET_DIR="$ROOT_DIR/installer/macos/pixen.iconset"
OUT_ICNS="$ROOT_DIR/assets/icons/pixen.icns"

if [ ! -f "$SRC_PNG" ]; then
    echo "error: $SRC_PNG not found" >&2
    exit 1
fi

rm -rf "$ICONSET_DIR"
mkdir -p "$ICONSET_DIR"

# macOS icns wants each of these exact sizes, standard + @2x retina.
for size in 16 32 128 256 512; do
    sips -z "$size" "$size" "$SRC_PNG" --out "$ICONSET_DIR/icon_${size}x${size}.png" >/dev/null
    double=$((size * 2))
    sips -z "$double" "$double" "$SRC_PNG" --out "$ICONSET_DIR/icon_${size}x${size}@2x.png" >/dev/null
done

iconutil -c icns "$ICONSET_DIR" -o "$OUT_ICNS"
rm -rf "$ICONSET_DIR"

echo "Created $OUT_ICNS"
