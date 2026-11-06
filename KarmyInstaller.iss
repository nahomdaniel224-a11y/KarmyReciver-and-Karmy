
#define MyAppName "Karmy by PC Karma"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "PC Karma"
#define MyAppExeName "KarmyReceiver.exe"

[Setup]
AppId={{B4D2C971-8E53-4D5C-A2F1-7C9B6E3D1052}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Karmy
DefaultGroupName={#MyAppName}
UninstallDisplayName={#MyAppName}
OutputDir=Output
OutputBaseFilename=Karmy-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "dist\KarmyReceiver\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Karmy"; Flags: postinstall nowait skipifsilent
