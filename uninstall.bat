@echo off
REM YouTube Downloader CLI - Windows uninstaller.
REM Removes the virtual environment and the PATH entry added by install.bat.
REM Optionally removes persistent app data (settings, history, logs).
REM
REM Usage: double-click this file, or run "uninstall.bat" from a terminal
REM        in the repository root.

setlocal
set "SCRIPT_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\uninstall.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
pause
endlocal
exit /b %EXIT_CODE%
