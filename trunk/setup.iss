; InnoSetup setup file for CodeCollaborator for UCM

; Copyright (c) 2006 by QUALCOMM INCORPORATED  All Rights Reserved.
; Miki Tebeka <mtebeka@qualcomm.com>
 
[Setup]
AppName = UCM CodeCollaborator
DefaultDirName = "{pf}\UCMCC"
DefaultGroupName = "UCMCC"
OutputDir = .

; This is created by the build system
#include "version.iss"

[Files]
Source: dist\*; DestDir: {app}

[Icons]
Name: "{group}\UCM CodeCollaborator"; Filename: "{app}\ucmcc.exe"
Name: "{group}\UCM CodeCollaborator - Baseline"; Filename: "{app}\ucmcc_baseline.exe"
Name: "{group}\Readme"; Filename: "{app}\README.html"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"
