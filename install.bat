@echo off
REM YouTube Downloader CLI - Windows installer.
REM Creates a virtual environment, installs the package, and adds the
REM `ytdownloader` / `ytcli` commands to your user PATH.
REM
REM Usage: double-click this file, or run "install.bat" from a terminal
REM        in the repository root.

setlocal
set "SCRIPT_DIR=%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\install.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if "%EXIT_CODE%"=="0" (
    echo Installation finished. Open a NEW terminal window and run: ytdownloader
) else (
    echo Installation failed. See the messages above for details.
)
pause
endlocal
exit /b %EXIT_CODE%
