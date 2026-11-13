@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "ROOT=%~dp0"
set "PY_DIR=%ROOT%python"
set "WEB_DIR=%ROOT%web"
set "VENV_PY=%PY_DIR%\myenv\Scripts\python.exe"

echo ============================================
echo  vue3-python-template
echo  backend : http://localhost:8000
echo  frontend: http://localhost:5173
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python not found. Install Python 3.10+ first.
  pause
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] npm not found. Install Node.js 18+ first.
  pause
  exit /b 1
)

if not exist "%VENV_PY%" (
  echo [1/4] Create python venv ...
  python -m venv "%PY_DIR%\myenv"
  if errorlevel 1 (
    echo [ERROR] python -m venv failed.
    pause
    exit /b 1
  )
) else (
  echo [1/4] venv already exists
)

echo [2/4] Install python deps if needed ...
"%VENV_PY%" -c "import django,corsheaders" 2>nul
if errorlevel 1 (
  "%VENV_PY%" -m pip install -r "%PY_DIR%\requirements.txt"
  if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
  )
)

if not exist "%WEB_DIR%\node_modules" (
  echo [3/4] npm install ...
  pushd "%WEB_DIR%"
  call npm install
  if errorlevel 1 (
    popd
    echo [ERROR] npm install failed.
    pause
    exit /b 1
  )
  popd
) else (
  echo [3/4] node_modules already exists
)

echo [4/4] Launch backend and frontend ...
start "template-backend" /D "%PY_DIR%" cmd /k start_backend.bat
start "template-web" /D "%WEB_DIR%" cmd /k start_web.bat

echo.
echo Started. Keep the two new windows open.
echo   backend   http://localhost:8000
echo   frontend  http://localhost:5173
echo   account   admin / 123456
echo.
echo Press any key to close this window...
pause >nul
exit /b 0
