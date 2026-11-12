@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "PORT=8000"
set "PYTHONUNBUFFERED=1"
set "PY=%~dp0myenv\Scripts\python.exe"

echo ============================================
echo  vue3-python-template  backend
echo  http://localhost:%PORT%
echo ============================================

if not exist "%PY%" (
  echo [ERROR] venv Python not found:
  echo   %PY%
  echo.
  echo Run the repository start.bat first.
  pause
  exit /b 1
)

echo [1/3] Free port %PORT% if occupied...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0free_port.ps1" -Port %PORT%
if errorlevel 2 (
  echo [ERROR] Port %PORT% is still in use.
  pause
  exit /b 2
)

echo [2/3] Check Python packages...
"%PY%" -c "import django,corsheaders" 2>nul
if errorlevel 1 (
  echo Installing requirements.txt ...
  "%PY%" -m pip install -r "%~dp0requirements.txt"
  if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
  )
)

echo [3/4] Apply database migrations...
"%PY%" manage.py migrate --noinput
"%PY%" seed_demo.py

echo [4/4] Starting API...
echo Press Ctrl+C to stop.
echo.
"%PY%" manage.py runserver 0.0.0.0:%PORT% --noreload
set "EC=%ERRORLEVEL%"
echo.
echo Server exited with code %EC%
pause
exit /b %EC%
