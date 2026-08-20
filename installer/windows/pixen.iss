; Inno Setup script for Pixen.
;
; Expects the PyInstaller onedir build to already exist at
; dist\Pixen\ (i.e. `pyinstaller Pixen.spec` has been run from the
; project root first). Produces Pixen-Setup.exe.
;
; The version is passed in from the build (CI passes /DPixenVersion=x.y.z
; from the git tag); it defaults to 0.0.0-dev for local test builds so
; the script also works stand-alone.
;
;   iscc installer\windows\pixen.iss /DPixenVersion=1.0.0

#ifndef PixenVersion
  #define PixenVersion "0.0.0-dev"
#endif

#define AppName "Pixen"
#define AppPublisher "Pixen"
#define AppExeName "Pixen.exe"
; Fixed GUID so upgrades replace the previous install instead of
; installing side-by-side. Do not change between releases.
#define AppId "{{6C6F5D2E-6B9E-4B7D-9C36-8F4C4D6A2E11}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#PixenVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
; Lets the user pick the install location (per spec section 19).
DisableDirPage=no
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}
; Per-user by default so admin rights aren't required; the installer
; still offers an "install for all users" choice via privilegesrequired.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\..\dist-installer
OutputBaseFilename=Pixen-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\..\assets\icons\pixen.ico
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
; Everything PyInstaller produced in dist\Pixen, folded flat into {app}.
Source: "..\..\dist\Pixen\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
