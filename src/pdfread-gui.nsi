; Copyright (c) 2007 Ashish Kulkarni
;
; Permission is hereby granted, free of charge, to any person obtaining a
; copy of this software and associated documentation files (the "Software"),
; to deal in the Software without restriction, including without limitation
; the rights to use, copy, modify, merge, publish, distribute, sublicense,
; and/or sell copies of the Software, and to permit persons to whom the
; Software is furnished to do so, subject to the following conditions:

; The above copyright notice and this permission notice shall be included in
; all copies or substantial portions of the Software.

; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
; AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
; FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
; DEALINGS IN THE SOFTWARE.

!include "MUI.nsh"

;--------------------------------
;General

!define GUI "PDFRead ${VERSION}"
Name    "${GUI}"
OutFile "..\pdfread-gui.exe"
InstallButtonText "Convert"
AutoCloseWindow true
BrandingText "${GUI}"
Caption "${GUI}"
MiscButtonText '<  Back' 'Convert'

;--------------------------------
;Pages

Page custom GetParams
Page custom GetCustomParams

!insertmacro MUI_PAGE_INSTFILES
  
!insertmacro MUI_LANGUAGE "English"

ReserveFile "pdfread-gui.ini"
ReserveFile "pdfread-gui-custom.ini"
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS

;--------------------------------
;Installer Sections

Section "Main Section"
  !insertmacro MUI_INSTALLOPTIONS_READ $R3 "pdfread-gui.ini" "Field 3" "State"
  !insertmacro MUI_INSTALLOPTIONS_READ $R4 "pdfread-gui.ini" "Field 4" "State"
  !insertmacro MUI_INSTALLOPTIONS_READ $R5 "pdfread-gui.ini" "Field 5" "State"
  !insertmacro MUI_INSTALLOPTIONS_READ $R6 "pdfread-gui.ini" "Field 6" "State"
  !insertmacro MUI_INSTALLOPTIONS_READ $R7 "pdfread-gui.ini" "Field 7" "State"
  !insertmacro MUI_INSTALLOPTIONS_READ $R8 "pdfread-gui.ini" "Field 8" "State"
  !insertmacro MUI_INSTALLOPTIONS_READ $R9 "pdfread-gui.ini" "Field 9" "State"
  
  StrCpy $R2 '-i $R4 -p $R5 -t "$R6"'
  StrCmp $R7 "" skip_author
  StrCpy $R2 '$R2 -a "$R7"'
skip_author:
  StrCmp $R7 "" skip_category
  StrCpy $R2 '$R2 -c "$R8"'
skip_category:
  StrCmp $R9 "" skip_output
  StrCpy $R2 '$R2 -o "$R9"'
skip_output:
  ReadIniStr $R1 "$PLUGINSDIR\option.ini" "config" "commandline"
  Exec '"$EXEDIR\pdfread-run.cmd" $R2 $R1 "$R3"'
SectionEnd

!macro ConfOption iscust optsect optval field item
  ReadIniStr  $R9 "$PLUGINSDIR\options.ini" "${optsect}" "${optval}"
  WriteIniStr "$PLUGINSDIR\pdfread-gui${iscust}.ini" "Field ${field}" "${item}" $R9
!macroend

!macro CustomParam option field
  ReadIniStr $R9 "$PLUGINSDIR\pdfread-gui.ini" "Field 5" "State"
  ReadIniStr $R8 "$PLUGINSDIR\options.ini" "$R9" "${option}"
  ReadIniStr $R7 "$PLUGINSDIR\pdfread-gui-custom.ini" "Field ${field}" "State"
  
  StrCmp $R7 $R8 +2
  StrCpy $R2 '$R2 --${option} $R7'
!macroend

;--------------------------------
;Installer Functions

Function .onInit
  !insertmacro MUI_INSTALLOPTIONS_EXTRACT "pdfread-gui.ini"
  !insertmacro MUI_INSTALLOPTIONS_EXTRACT "pdfread-gui-custom.ini"

  Call GetParameters
  Pop  $R0
  StrCmp $R0 "" options
  IfFileExists $R0 0 options
  !insertmacro MUI_INSTALLOPTIONS_WRITE "pdfread-gui.ini" "Field 3" "State" $R0
options:
  nsExec::ExecToLog '"$EXEDIR\bin\pdfread.exe" --dump-profiles "$PLUGINSDIR\options.ini"'
  IfFileExists "$PLUGINSDIR\options.ini" 0 skip

  !insertmacro ConfOption '' 'config' 'formats'         '4' 'ListItems'
  !insertmacro ConfOption '' 'config' 'default_format'  '4' 'State'
  !insertmacro ConfOption '' 'config' 'profiles'        '5' 'ListItems'
  !insertmacro ConfOption '' 'config' 'default_profile' '5' 'State'
  
  !insertmacro ConfOption '-custom' 'config' 'dpi'          '3' 'State'
  !insertmacro ConfOption '-custom' 'config' 'autocontrast' '4' 'State'
  !insertmacro ConfOption '-custom' 'config' 'rotation'     '8' 'ListItems'
skip:
FunctionEnd

Function GetParams
  !insertmacro MUI_HEADER_TEXT "${GUI}" "Please enter the conversion details."
  !insertmacro MUI_INSTALLOPTIONS_DISPLAY "pdfread-gui.ini"

FunctionEnd

Function GetCustomParams
  StrCpy $R2 ""

  ReadIniStr $R0 "$PLUGINSDIR\pdfread-gui.ini" "Field 10" "State"
  IntCmp $R0 0 skip_custom
  
  ReadIniStr $R1 "$PLUGINSDIR\pdfread-gui.ini" "Field 5" "State"
  
  IfFileExists "$PLUGINSDIR\options.ini" 0 display
  !insertmacro ConfOption '-custom' '$R1' 'hres'    '6'  'State'
  !insertmacro ConfOption '-custom' '$R1' 'vres'    '7'  'State'
  !insertmacro ConfOption '-custom' '$R1' 'rotate'  '8'  'State'
  !insertmacro ConfOption '-custom' '$R1' 'colors'  '9'  'State'
  !insertmacro ConfOption '-custom' '$R1' 'overlap' '10' 'State'
  !insertmacro ConfOption '-custom' '$R1' 'nosplit' '11' 'State'
display:

  !insertmacro MUI_HEADER_TEXT "${GUI}" "Please enter the custom parameters."
  !insertmacro MUI_INSTALLOPTIONS_DISPLAY "pdfread-gui-custom.ini"
  
  ; create the custom parameter command line
  !insertmacro CustomParam 'hres'    '6'
  !insertmacro CustomParam 'vres'    '7'
  !insertmacro CustomParam 'rotate'  '8'
  !insertmacro CustomParam 'colors'  '9'
  !insertmacro CustomParam 'overlap' '10'
  
  ReadIniStr $R9 "$PLUGINSDIR\pdfread-gui-custom.ini" "Field 11" "State"
  IntCmp $R9 0 skip_custom
  StrCpy $R2 '$R2 --nosplit '
  
skip_custom:
  WriteIniStr "$PLUGINSDIR\option.ini" "config" "commandline" $R2
FunctionEnd

Function GetParameters
 
  Push $R0
  Push $R1
  Push $R2
  Push $R3
  
  StrCpy $R2 1
  StrLen $R3 $CMDLINE
  
  ;Check for quote or space
  StrCpy $R0 $CMDLINE $R2
  StrCmp $R0 '"' 0 +3
    StrCpy $R1 '"'
    Goto loop
  StrCpy $R1 " "
  
  loop:
    IntOp $R2 $R2 + 1
    StrCpy $R0 $CMDLINE 1 $R2
    StrCmp $R0 $R1 get
    StrCmp $R2 $R3 get
    Goto loop
  
  get:
    IntOp $R2 $R2 + 1
    StrCpy $R0 $CMDLINE 1 $R2
    StrCmp $R0 " " get
    StrCpy $R0 $CMDLINE "" $R2
  
  Pop $R3
  Pop $R2
  Pop $R1
  Exch $R0
 
FunctionEnd