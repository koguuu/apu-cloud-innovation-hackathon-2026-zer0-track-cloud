# PowerShell Launcher for Campus Wi-Fi Health AIOps Platform
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   Starting Campus Wi-Fi Health AIOps Platform..." -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$PythonExe = "python"
if (Test-Path "$ScriptDir\.venv\bin\python.exe") {
    $PythonExe = "$ScriptDir\.venv\bin\python.exe"
} elseif (Test-Path "$ScriptDir\.venv\Scripts\python.exe") {
    $PythonExe = "$ScriptDir\.venv\Scripts\python.exe"
}

Write-Host "Using Python: $PythonExe" -ForegroundColor Green
Write-Host "Dashboard will open at: http://localhost:8080" -ForegroundColor Yellow
Write-Host ""

& $PythonExe start.py --port 8080
