#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -x .venv/bin/python ]; then
  if command -v python3.12 >/dev/null 2>&1; then PY=python3.12; else PY=python3; fi
  "$PY" -m venv .venv
fi
source .venv/bin/activate
python scripts/check_bundled_hactool.py
if ! python -m pip --version >/dev/null 2>&1; then python -m ensurepip --upgrade; fi
# pip checks installed versions and downloads only missing/outdated requirements.
python -m pip install --disable-pip-version-check --no-compile -r requirements.txt
pyinstaller --noconfirm --clean --windowed --onedir --name HactoolGUI --icon assets/icon.png --add-data 'assets/icon.png:assets' --add-data 'src/extract.py:src' --add-binary 'bin/linux/hactool:bin/linux' --paths src src/main.py
PKG="build/deb/hactoolgui_3.7.0"
mkdir -p "$PKG/DEBIAN" "$PKG/opt/hactoolgui" "$PKG/usr/share/applications" "$PKG/usr/share/icons/hicolor/256x256/apps" "$PKG/usr/bin"
cp -a dist/HactoolGUI/. "$PKG/opt/hactoolgui/"
cp assets/icon.png "$PKG/usr/share/icons/hicolor/256x256/apps/hactoolgui.png"
cat > "$PKG/DEBIAN/control" <<'EOF'
Package: hactoolgui
Version: 3.7.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: ALEX GARCI
Description: Cross-platform graphical frontend for hactool
EOF
ARCH="$(dpkg --print-architecture)"
sed -i "s/Architecture: amd64/Architecture: $ARCH/" "$PKG/DEBIAN/control"
cat > "$PKG/usr/share/applications/hactoolgui.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Hactool GUI
Exec=/opt/hactoolgui/HactoolGUI
Icon=hactoolgui
Categories=Utility;
Terminal=false
EOF
ln -s /opt/hactoolgui/HactoolGUI "$PKG/usr/bin/hactoolgui"
mkdir -p dist
dpkg-deb --build --root-owner-group "$PKG" "dist/hactoolgui_3.7.0_${ARCH}.deb"
echo "Listo: dist/hactoolgui_3.7.0_${ARCH}.deb"
