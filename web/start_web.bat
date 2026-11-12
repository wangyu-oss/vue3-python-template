@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================
echo  vue3-python-template  web
echo  http://localhost:5173
echo ============================================

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm not found. Install Node.js 18+ first.
  pause
  exit /b 1
)

if not exist "%~dp0node_modules" (
  echo [1/2] npm install ...
  call npm install
  if errorlevel 1 (
    echo [ERROR] npm install failed.
    pause
    exit /b 1
  )
)

echo [2/2] npm run dev
echo Press Ctrl+C to stop.
echo.
call npm run dev
set "EC=%ERRORLEVEL%"
echo.
echo Dev server exited with code %EC%
pause
exit /b %EC%
