[Setup]
AppName=VOICE FX PRO
AppVersion=1.0.5
DefaultDirName={pf}\VoiceFX
DefaultGroupName=VOICE FX PRO
OutputDir=installer
OutputBaseFilename=VoiceFX-Setup
SetupIconFile=assets\icons\icon.ico
UninstallDisplayIcon={app}\VoiceFX.exe
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Files]
Source: "dist\VoiceFX\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
Source: "vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; Check: IsVCRedistNeeded

[Icons]
Name: "{commondesktop}\VOICE FX PRO"; Filename: "{app}\VoiceFX.exe"; IconFilename: "{app}\VoiceFX.exe"
Name: "{group}\VOICE FX PRO"; Filename: "{app}\VoiceFX.exe"; IconFilename: "{app}\VoiceFX.exe"

[Run]
Filename: "{tmp}\vc_redist.x64.exe"; Parameters: "/install /quiet /norestart"; StatusMsg: "Instalowanie Microsoft Visual C++ Redistributable..."; Check: IsVCRedistNeeded; Flags: waituntilterminated

[Code]
function IsVCRedistNeeded(): Boolean;
var
  installed: Cardinal;
begin
  if RegQueryDWordValue(
       HKLM,
       'SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64',
       'Installed',
       installed) then
  begin
    Result := installed <> 1;
  end
  else
  begin
    Result := True;
  end;
end;
