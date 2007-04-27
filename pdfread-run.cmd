@echo off
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