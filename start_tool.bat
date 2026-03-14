@echo off
setlocal

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

where py >nul 2>nul
if %errorlevel%==0 (
    py ui.py
    goto :eof
)

where python >nul 2>nul
if %errorlevel%==0 (
    python ui.py
    goto :eof
)

echo [ERROR] Python not found. Please install Python 3.9+ and add it to PATH.
pause
