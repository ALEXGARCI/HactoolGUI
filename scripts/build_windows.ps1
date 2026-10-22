$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
}
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
if (-not (Test-Path 'bin\windows\hactool.exe')) {
    throw 'Falta bin/windows/hactool.exe. El proyecto debe incluir este archivo; no se descarga durante la compilación.'
}
& $python scripts/check_bundled_hactool.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& $python -m pip install --disable-pip-version-check --no-compile -r requirements.txt
& $python -m PyInstaller --noconfirm --clean --windowed --onefile --name HactoolGUI --icon assets/icon.ico --add-data 'assets/icon.png;assets' --add-data 'src/extract.py;src' --add-binary 'bin/windows/hactool.exe;bin/windows' --paths src src/main.py
Write-Host 'Listo: dist\HactoolGUI.exe (portable). Para instalador, ejecuta scripts\installer_windows.iss con Inno Setup.'
