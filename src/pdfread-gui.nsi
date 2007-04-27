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

!define GUI "PDFRead GUI ${VERSION}"
Name    "${GUI}"
OutFile "..\pdfread-gui.exe"
InstallButtonText "Convert"
AutoCloseWindow true
BrandingText "${GUI}"
Caption "${GUI}"

;--------------------------------
;Pages

Page custom GetConversionParameters

!insertmacro MUI_PAGE_INSTFILES
  
!insertmacro MUI_LANGUAGE "English"

ReserveFile "pdfread-gui.ini"
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS

;--------------------------------
;Installer Sections

Section "Main Section"
SectionEnd

!macro OptionalParam num param
  !insertmacro MUI_INSTALLOPTIONS_READ $R9 "pdfread-gui.ini" "Field ${num}" "State"
  Strcmp $R9 "" +2
  StrCpy $R2 '$R2 ${param} "$R9"'
!macroend

!macro DefaultParam num param def
  !insertmacro MUI_INSTALLOPTIONS_READ $R9 "pdfread-gui.ini" "Field ${num}" "State"
  Strcmp $R9 "" +3
  Strcmp $R9 "${def}" +2
  StrCpy $R2 '$R2 ${param} "$R9"'
!macroend

!macro Flag num name
  !insertmacro MUI_INSTALLOPTIONS_READ $R9 "pdfread-gui.ini" "Field ${num}" "State"
  IntCmpU $R9 0 +2
  StrCpy $R2 '$R2 ${name}'
!macroend

!macro Tip num tooltip
  FindWindow $3 "#32770" "" $HWNDPARENT
  IntOp $5 1199 + ${num}
  GetDlgItem $1 $3 $5
  ToolTips::Modern $1 0 "" "${tooltip}"
!macroend

Function .onInit
  !insertmacro MUI_INSTALLOPTIONS_EXTRACT "pdfread-gui.ini"

  Call GetParameters
  Pop  $R0
  StrCmp $R0 "" skip
  IfFileExists $R0 0 skip
  !insertmacro MUI_INSTALLOPTIONS_WRITE "pdfread-gui.ini" "Field 3" "State" $R0
skip:
FunctionEnd

Function GetConversionParameters
start:
  !insertmacro MUI_HEADER_TEXT "${GUI}" "Please enter the conversion details."
  !insertmacro MUI_INSTALLOPTIONS_INITDIALOG "pdfread-gui.ini"
  ; tooltips
  !insertmacro Tip 3 "This is the file that you want to use for conversion."
  !insertmacro Tip 5 "Input document format."
  !insertmacro Tip 6 "Title of the generated eBook"
  !insertmacro Tip 7 "Author of the generated eBook"
  !insertmacro Tip 8 "Category of the generated eBook"
  !insertmacro Tip 9 "The output filename (you will have to enter appropriate file extension)"
  !insertmacro Tip 11 "The page layout mode. Use default to use the mode defined in the profile."
  !insertmacro Tip 12 "Profile to use during conversion"
  !insertmacro Tip 13 "Disable the cropping stage during conversion"
  !insertmacro Tip 14 "Disable the image dilation stage during conversion"
  !insertmacro Tip 15 "Disable the edge enhancement stage during conversion"
  !insertmacro Tip 16 "Start conversion from this page"
  !insertmacro Tip 17 "End conversion at this page"
  !insertmacro Tip 18 "All whitespace areas larger than this percentage will be cropped. Reduce if you want more aggressive cropping."
  !insertmacro Tip 19 "Each page will be rendered at this DPI for dilation. Increase this to reduce the dilation effect."
  !insertmacro Tip 20 "Edge enhacement level. Increase for more sharper text, decrease for more smoother text."
  !insertmacro Tip 21 "The command line arguments to pass to unpaper"
  !insertmacro Tip 22 "Each generated PNG will be optimized for maximum compression (can take some time)"
  !insertmacro MUI_INSTALLOPTIONS_SHOW
  StrCmp $MUI_TEMP1 "cancel" finish


  !insertmacro MUI_INSTALLOPTIONS_READ $R3 "pdfread-gui.ini" "Field 4" "State"
  !insertmacro MUI_INSTALLOPTIONS_READ $R4 "pdfread-gui.ini" "Field 5" "State"
  !insertmacro MUI_INSTALLOPTIONS_READ $R5 "pdfread-gui.ini" "Field 10" "State"

  StrCpy $R2 '-p $R5 -i $R3 -t "$R4" '
  !insertmacro OptionalParam 6 '-a'
  !insertmacro OptionalParam 7 '-c'
  !insertmacro OptionalParam 8 '-o'
  
  !insertmacro OptionalParam 14 '--first-page'
  !insertmacro OptionalParam 15 '--last-page'
  
  !insertmacro Flag 11 '--no-crop'
  !insertmacro Flag 12 '--no-dilate'
  !insertmacro Flag 13 '--no-enhance'
  !insertmacro Flag 20 '--optimize'
  
  !insertmacro DefaultParam 16 '--crop-percent' '2.0'
  !insertmacro DefaultParam 17 '--dpi' '300'
  !insertmacro DefaultParam 18 '--edge-level' '5'
  !insertmacro DefaultParam 9  '-m' 'default'
  
  !insertmacro OptionalParam 19 '-u'
  
  !insertmacro MUI_INSTALLOPTIONS_READ $R3 "pdfread-gui.ini" "Field 3" "State"
  Strcpy $R2 '$R2 "$R3"'
  Exec '"$EXEDIR\pdfread-run.cmd" $R2'
  Goto start
finish:

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
