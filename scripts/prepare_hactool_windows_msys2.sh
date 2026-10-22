#!/usr/bin/env bash
# Ejecutar dentro de MSYS2 MinGW64 (no PowerShell). GitHub Actions lo hace automáticamente.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -s bin/windows/hactool.exe ]; then echo 'hactool Windows incluido: se reutiliza'; exit 0; fi
mkdir -p build/upstream bin/windows
if [ ! -d build/upstream/hactool/.git ]; then
 git clone --depth 1 https://github.com/SciresM/hactool.git build/upstream/hactool
fi
cd build/upstream/hactool
[ -f config.mk ] || cp config.mk.template config.mk
make -j2
cp hactool.exe ../../../bin/windows/hactool.exe
