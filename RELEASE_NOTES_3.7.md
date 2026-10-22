# Hactool GUI 3.7.0 — Correcciones

- Validación inmediata al elegir archivos desde **Examinar** o terminar de editar la ruta; mensaje visible y registro con `VALIDADO` / `RECHAZADO`.
- Comprobación cruzada para impedir seleccionar el mismo archivo como prod.keys y title.keys.
- Validación de extensiones según modo y comprobación de contenido de claves sin imprimir secretos.
- La inspección NCA ya no utiliza `-i`; una sección ilegible no debe detener la exploración de otros NCA.
- Se prueban los NCA de tipo Program en secuencia, registrando fallos sin declarar éxito prematuramente.
- Los ejecutables nativos hactool de macOS ARM64, Windows x64 y Linux x64 se conservan en `bin/`.
- Tests básicos de validación: `python3 -m unittest discover -s tests -v`.

## Estado de verificación

Probado aquí: compilación de sintaxis Python, 4 pruebas unitarias, presencia y formato de los tres ejecutables.
**Pendiente:** compilar las interfaces en macOS/Windows/Linux y confirmar extracción completa de un NSP real en el equipo del usuario. La versión de hactool y el material de claves pueden afectar el resultado.

## Instalar desde código fuente en macOS

```bash
cd '/Users/alexgarci/Downloads/HactoolGUI_3.7_GitHub'
chmod +x scripts/build_macos.sh
./scripts/build_macos.sh
open 'dist/HactoolGUI_3.7.0_macOS.dmg'
```

Windows: `powershell -ExecutionPolicy Bypass -File scripts\\build_windows.ps1` y luego compilar `scripts/installer_windows.iss` con Inno Setup.
Linux Debian/Ubuntu x64: `bash scripts/build_linux.sh`.
GitHub: ejecutar **Actions → Build installers (Windows macOS Linux)**. Los tres binarios se empaquetan desde el repositorio; no se buscan en otras ubicaciones.

Las claves `prod.keys` y `title.keys` no se distribuyen. Usa únicamente archivos y claves que estés autorizado a utilizar.
