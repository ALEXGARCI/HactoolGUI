#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -x bin/linux/hactool ]; then echo 'hactool Linux incluido: se reutiliza'; exit 0; fi
if ! command -v git >/dev/null || ! command -v make >/dev/null || ! command -v gcc >/dev/null; then
 echo 'Faltan herramientas de compilación: git, make y gcc. Instala build-essential y git.' >&2; exit 1
fi
mkdir -p build/upstream bin/linux
if [ ! -d build/upstream/hactool/.git ]; then
 git clone --depth 1 https://github.com/SciresM/hactool.git build/upstream/hactool
fi
cd build/upstream/hactool
[ -f config.mk ] || cp config.mk.template config.mk
make -j2
cp hactool ../../../bin/linux/hactool
chmod +x ../../../bin/linux/hactool
file ../../../bin/linux/hactool || true
