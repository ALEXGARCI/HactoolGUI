<div align="center">

<img src="assets/icon.png" alt="Hactool GUI Logo" width="180">

</div>

# Hactool GUI 3.6 — ALEX GARCI

Aplicación gráfica para macOS Apple Silicon, Windows x64 y Linux x64. Interfaz Qt/PySide6 con temas azul oscuro y claro. El ejecutable **hactool viene dentro de este repositorio** y se empaqueta en el instalador: el usuario final no instala hactool, Python ni Qt.

## Contenido incluido (sin descargas de hactool)

- `bin/macos/hactool`: Mach-O ARM64.
- `bin/windows/hactool.exe`: PE x64.
- `bin/linux/hactool`: ELF x64 dinámico, compilado en Ubuntu 22.04.
- `src/`: interfaz y motor de extracción.
- `assets/`: iconos.
- `scripts/`: scripts de empaquetado y validación.
- `.github/workflows/build.yml`: compilación en los tres sistemas mediante GitHub Actions.

**Ningún script de empaquetado descarga ni busca hactool fuera del repositorio.** Si falta el binario local, la compilación falla claramente. Los scripts sí instalan dependencias **de desarrollo** de Python cuando faltan. Los instaladores resultantes las incluyen. Las claves `prod.keys` y, cuando correspondan, `title.keys` son archivos personales que debe proporcionar cada usuario.

## Compilar macOS ARM64

Requiere macOS Apple Silicon, Python 3.12 y herramientas de línea de comandos de Xcode. En la raíz del proyecto:

```bash
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
open dist/HactoolGUI_3.6.1_macOS.dmg
```

## Compilar Windows x64

Requiere Windows x64, Python 3.12, y **Inno Setup 6** para crear el instalador con asistente. En PowerShell, desde la raíz:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
& 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' scripts\installer_windows.iss
```

Resultados: `dist/HactoolGUI.exe` (portable) y `dist/HactoolGUI_3.6.1_Windows_Setup.exe` (instalador). El script no necesita MSYS2 ni compilar hactool: `bin/windows/hactool.exe` ya está incluido.

## Compilar Linux x64 (Ubuntu/Debian)

Requiere Python 3.12, venv, `dpkg-deb` y bibliotecas gráficas del sistema. Por ejemplo, en Ubuntu:

```bash
sudo apt-get update
sudo apt-get install -y python3.12 python3.12-venv python3-pip dpkg-dev libgl1 libegl1 libxkbcommon0
chmod +x scripts/build_linux.sh bin/linux/hactool
./scripts/build_linux.sh
```

Resultado: `dist/hactoolgui_3.6.1_amd64.deb`. El binario Linux se enlazó dinámicamente: en distribuciones antiguas o distintas puede necesitar bibliotecas compatibles. Se recomienda validar en Ubuntu 22.04 y 24.04 antes de distribuir.

## Compilar todos con GitHub Actions

1. Sube **el contenido de la carpeta del proyecto** a un repositorio de GitHub. Incluye `.github/` y los tres archivos `bin/*/hactool*`.
2. Ve a **Actions → Build installers (Windows macOS Linux) → Run workflow**.
3. Descarga los artefactos generados: DMG, EXE/Setup y DEB.
4. Comprueba instalación y extracción en cada sistema antes de publicar un Release.

**Importante:** macOS utiliza el runner `macos-15-arm64`; un runner Intel no puede ejecutar el hactool ARM64 incluido. Windows y Linux usan runners x64.

## Verificación local

```bash
python3 scripts/check_bundled_hactool.py
```

Comprueba el ejecutable **del sistema actual**, no los otros dos. No incluye claves ni contenido de juegos. Para usarlo, proporciona únicamente archivos sobre los que tengas derechos o autorización.

## Créditos y redistribución

Interfaz e integración: **ALEX GARCI**. Motor: [hactool de SciresM y colaboradores](https://github.com/SciresM/hactool). También se utilizan Python, Qt/PySide6 y PyInstaller. Revisa `THIRD_PARTY.md` y las licencias originales antes de distribuir binarios; en particular, las obligaciones de LGPL de Qt.

## Alcance de pruebas

Se verificó que los tres binarios están dentro del ZIP y que el código Python compila sintácticamente. **No se ejecutaron aquí los instaladores en macOS, Windows o Linux**. La primera ejecución de GitHub Actions puede requerir ajustes y no debe considerarse una publicación estable sin pruebas.

## Versión 3.7.0

Consulta [RELEASE_NOTES_3.7.md](RELEASE_NOTES_3.7.md) para correcciones, pruebas y comandos actualizados.
