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

SetCompress force
SetCompressor /solid lzma
AutoCloseWindow true
!include "MUI.nsh"

;--------------------------------
;General

  ;Name and file
  Name "PDFRead ${VERSION}"
  OutFile "..\pdfread-${VERSION}.exe"

  ;Default installation folder
  InstallDir "$PROGRAMFILES\PDFRead"


;--------------------------------
;Interface Settings

!define MUI_ABORTWARNING
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
;Languages

!insertmacro MUI_LANGUAGE "English"

;--------------------------------
;Installer Sections

Section "Install Section" SecInstall

  SetOutPath "$INSTDIR"

  File /r /x ".svn" *.*

  ;Create uninstaller
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PDFRead" "DisplayName" "PDFRead ${VERSION}"
  WriteRegStr HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PDFRead" "UninstallString" "$INSTDIR\uninstall.exe"
  
  ClearErrors
  ReadRegStr $R0 HKCR ".pdf" ""
  IfErrors skip_context
  WriteRegStr HKCR "$R0\shell\pdfread" "" "&PDFRead Conversion"
  WriteRegStr HKCR "$R0\shell\pdfread\command" "" '"$INSTDIR\pdfread-gui.exe" %1'
skip_context:
  WriteRegStr HKCR "AcroExch.Document.7\shell\pdfread" "" "&PDFRead Conversion"
  WriteRegStr HKCR "AcroExch.Document.7\shell\pdfread\command" "" '"$INSTDIR\pdfread-gui.exe" %1'
  SetShellVarContext all
  CreateShortCut "$SMPROGRAMS\PDFRead.lnk" "$INSTDIR\pdfread-gui.exe"
  ExecShell "" "$INSTDIR\doc\index.html"

  WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall"
  DeleteRegKey HKLM "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\PDFRead"
  RMDir /r "$INSTDIR"
  SetShellVarContext all
  Delete "$SMPROGRAMS\PDFRead.lnk"
  ClearErrors
  ReadRegStr $R0 HKCR ".pdf" ""
  IfErrors skip_context
  DeleteRegKey  HKCR "$R0\shell\pdfread"
skip_context:
  DeleteRegKey  HKCR "AcroExch.Document.7\shell\pdfread"
SectionEnd
