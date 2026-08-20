#!/bin/bash
# Build Pixen-Linux-x86_64.AppImage from the PyInstaller onedir build.
# Run on Linux, after `pyinstaller Pixen.spec` has produced dist/Pixen/.
#
# Downloads appimagetool on first run (cached in installer/linux/tools/)
# -- no other external dependency. The AppImage bundles dist/Pixen as-is,
# so it carries its own Python/Qt and does not require Python installed
# on the target system.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DIST_DIR="$ROOT_DIR/dist/Pixen"
TOOLS_DIR="$ROOT_DIR/installer/linux/tools"
APPDIR="$ROOT_DIR/installer/linux/AppDir"
OUT_DIR="$ROOT_DIR/dist-installer"
APPIMAGETOOL="$TOOLS_DIR/appimagetool-x86_64.AppImage"

if [ ! -d "$DIST_DIR" ]; then
    echo "error: $DIST_DIR not found -- run 'pyinstaller Pixen.spec' first" >&2
    exit 1
fi

mkdir -p "$TOOLS_DIR" "$OUT_DIR"

if [ ! -x "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    curl -L -o "$APPIMAGETOOL" \
        "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x "$APPIMAGETOOL"
fi

rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/512x512/apps"

cp -R "$DIST_DIR/." "$APPDIR/usr/bin/"

# AppRun launches the bundled binary regardless of where the AppImage
# is mounted -- no absolute paths.
cat > "$APPDIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "$HERE/usr/bin/Pixen" "$@"
EOF
chmod +x "$APPDIR/AppRun"

cp "$ROOT_DIR/packaging/pixen.desktop" "$APPDIR/pixen.desktop"
cp "$ROOT_DIR/packaging/pixen.desktop" "$APPDIR/usr/share/applications/pixen.desktop"
cp "$ROOT_DIR/assets/icons/pixen.png" "$APPDIR/pixen.png"
cp "$ROOT_DIR/assets/icons/pixen.png" "$APPDIR/usr/share/icons/hicolor/512x512/apps/pixen.png"

ARCH=x86_64 "$APPIMAGETOOL" "$APPDIR" "$OUT_DIR/Pixen-Linux-x86_64.AppImage"

echo "Created $OUT_DIR/Pixen-Linux-x86_64.AppImage"
