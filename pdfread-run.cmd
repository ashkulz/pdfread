@echo off
set PATH=%~dp0bin;%~dp0bin\djvu;%~dp0bin\tiff;%~dp0bin\misc;%~dp0gs8.54\bin;%PATH%
set GS_LIB=%~dp0gs8.54\lib;%~dp0gs8.54\fonts
set MAGICK_CONFIGURE_PATH=%~dp0bin\imagemagick
if '%1' == '' goto shell
title PDFRead Conversion
echo Command Line
echo ============
echo.
echo "%~dp0bin\pdfread" %*
echo.
"%~dp0bin\pdfread" %*
pause
exit /b %errorlevel%

:shell
echo No file specified, starting command shell.
cmd /k title PDFRead Shell
exit /b 0