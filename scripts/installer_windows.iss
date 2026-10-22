#define MyAppName "Hactool GUI"
#define MyAppVersion "3.6.0"
#define MyAppPublisher "ALEX GARCI"
[Setup]
AppId={{5FAD40BD-BABE-45F3-9895-2AA84EAFB68E}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Hactool GUI
DefaultGroupName=Hactool GUI
OutputDir=..\dist
OutputBaseFilename=HactoolGUI_3.6_Windows_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\icon.ico
[Files]
Source: "..\dist\HactoolGUI.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\Hactool GUI"; Filename: "{app}\HactoolGUI.exe"
Name: "{autodesktop}\Hactool GUI"; Filename: "{app}\HactoolGUI.exe"; Tasks: desktopicon
[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked
[Run]
Filename: "{app}\HactoolGUI.exe"; Description: "Abrir Hactool GUI"; Flags: nowait postinstall skipifsilent
