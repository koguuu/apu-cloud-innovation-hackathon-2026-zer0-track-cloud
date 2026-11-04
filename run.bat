@echo off
title Campus Wi-Fi Health - Autonomous AIOps
echo ======================================================================
echo    Starting Campus Wi-Fi Health AIOps Platform...
echo ======================================================================

set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

if exist ".venv\bin\python.exe" (
    set "PYTHON_EXE=.venv\bin\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXE=python"
)

echo Using Python: %PYTHON_EXE%
echo Dashboard will be available at: http://localhost:8080
echo.
"%PYTHON_EXE%" start.py --port 8080
pause
