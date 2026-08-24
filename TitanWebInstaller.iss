[Setup]
AppId=TitanWeb
AppName=Titan Web
AppVersion=1.0.0
AppPublisher=ООО «Центр Программных Инноваций»

DefaultDirName={localappdata}\TitanWeb
DefaultGroupName=Titan Web
PrivilegesRequired=lowest

OutputDir=installer
OutputBaseFilename=TitanWeb_Setup_1.0.0

SetupIconFile=assets\TW.ico
UninstallDisplayIcon={app}\TitanWeb.exe

LicenseFile=license_TitanWeb.rtf

VersionInfoVersion=1.0.0.0
VersionInfoProductVersion=1.0.0.0
VersionInfoDescription=Установщик Titan Web
VersionInfoProductName=Titan Web
VersionInfoCompany=ООО «Центр Программных Инноваций»
VersionInfoCopyright=© 2026 ООО «Центр Программных Инноваций»

Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ShowLanguageDialog=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; \
    Description: "Создать ярлык на рабочем столе"; \
    Flags: unchecked

Name: "autostart"; \
    Description: "Запускать Titan Web при входе в Windows"; \
    Flags: unchecked


[Files]
Source: "dist\TitanWeb\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

Source: "license_TitanWeb.rtf"; \
    DestDir: "{app}"; \
    DestName: "license_TitanWeb.rtf"; \
    Flags: ignoreversion



[Icons]
Name: "{autoprograms}\Titan Web"; \
    Filename: "{app}\TitanWeb.exe"; \
    WorkingDir: "{app}"

Name: "{autodesktop}\Titan Web"; \
    Filename: "{app}\TitanWeb.exe"; \
    WorkingDir: "{app}"; \
    Tasks: desktopicon

Name: "{userstartup}\Titan Web"; \
    Filename: "{app}\TitanWeb.exe"; \
    WorkingDir: "{app}"; \
    Tasks: autostart


[Run]
Filename: "{app}\TitanWeb.exe"; \
    Description: "Запустить Titan Web"; \
    WorkingDir: "{app}"; \
    Flags: nowait postinstall skipifsilent