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
mkdir -p build/icon.iconset
for s in 16 32 128 256 512; do
  sips -z "$s" "$s" assets/icon.png --out "build/icon.iconset/icon_${s}x${s}.png" >/dev/null
  if [ "$s" -lt 512 ]; then
    d=$((s*2)); sips -z "$d" "$d" assets/icon.png --out "build/icon.iconset/icon_${s}x${s}@2x.png" >/dev/null
  fi
done
iconutil -c icns build/icon.iconset -o build/icon.icns
pyinstaller --noconfirm --clean --windowed --name 'Hactool GUI' --icon build/icon.icns --add-data 'assets/icon.png:assets' --add-data 'src/extract.py:src' --add-binary 'bin/macos/hactool:bin/macos' --paths src src/main.py
mkdir -p build/dmg_contents
rm -rf 'build/dmg_contents/Hactool GUI.app'
cp -R 'dist/Hactool GUI.app' build/dmg_contents/
ln -sfn /Applications build/dmg_contents/Applications
hdiutil create -volname 'Hactool GUI' -srcfolder build/dmg_contents -ov -format UDZO 'dist/HactoolGUI_3.7.0_macOS.dmg'
echo 'Listo: dist/HactoolGUI_3.7.0_macOS.dmg'
