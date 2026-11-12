@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo Stopping template backend and frontend ...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0python\free_port.ps1" -Port 8000
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0python\free_port.ps1" -Port 5173
echo Done.
exit /b 0
