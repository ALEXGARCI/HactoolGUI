#!/usr/bin/env python3
"""Validate the platform-native, vendored hactool; never download it."""
import os, platform, subprocess, sys
from pathlib import Path
root = Path(__file__).resolve().parent.parent
system = {'Darwin':'macos','Windows':'windows','Linux':'linux'}.get(platform.system())
if system is None: sys.exit('Sistema operativo no soportado.')
if platform.machine().lower() not in ({'arm64','aarch64'} if system == 'macos' else {'x86_64','amd64'}):
    sys.exit(f'Arquitectura no soportada: {platform.system()} {platform.machine()}')
exe = root / 'bin' / system / ('hactool.exe' if system == 'windows' else 'hactool')
if not exe.is_file() or exe.stat().st_size < 10000:
    sys.exit(f'Falta hactool incluido: {exe}')
if system != 'windows' and not os.access(exe, os.X_OK):
    sys.exit(f'Sin permiso de ejecución: {exe} (chmod +x)')
try:
    proc = subprocess.run([str(exe)], capture_output=True, timeout=10)
except (OSError, subprocess.TimeoutExpired) as err:
    sys.exit(f'No se puede iniciar el hactool incluido: {err}')
print(f'OK: hactool incluido ({system} / {platform.machine()}, {exe.stat().st_size} bytes; salida {proc.returncode})')
