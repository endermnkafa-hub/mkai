@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"
set "PYTHON_EXE=%ROOT%.venv-1\Scripts\python.exe"
set "BACKEND_LOG=%ROOT%logs\backend.log"
set "FRONTEND_LOG=%ROOT%logs\frontend.log"

if not exist "%BACKEND_DIR%" (
  echo Backend folder not found.
  pause
  exit /b 1
)

if not exist "%FRONTEND_DIR%" (
  echo Frontend folder not found.
  pause
  exit /b 1
)

if not exist "%PYTHON_EXE%" (
  echo Virtual environment not found. Please run the project setup first.
  pause
  exit /b 1
)

if not exist "%ROOT%logs" mkdir "%ROOT%logs"

for /f "usebackq tokens=5" %%a in (`netstat -ano ^| findstr /R /C:":8000 " ^| findstr /R /C:"LISTENING"`) do (
  echo Stopping existing backend process on port 8000: %%a
  taskkill /F /PID %%a >nul 2>&1
)

for /f "usebackq tokens=5" %%a in (`netstat -ano ^| findstr /R /C:":3001 " ^| findstr /R /C:"LISTENING"`) do (
  echo Stopping existing frontend process on port 3001: %%a
  taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

rem start "" http://127.0.0.1:3001/
start /B "" cmd /c "cd /d "%BACKEND_DIR%" && "%PYTHON_EXE%" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > "%BACKEND_LOG%" 2>&1"
start /B "" cmd /c "cd /d "%FRONTEND_DIR%" && npm run dev -- --hostname 127.0.0.1 --port 3001 > "%FRONTEND_LOG%" 2>&1"

echo MKAI is starting...
echo Backend log: %BACKEND_LOG%
echo Frontend log: %FRONTEND_LOG%
echo Backend: http://127.0.0.1:8000/health
echo Frontend: http://127.0.0.1:3001/

echo.
echo Waiting for services to come up...
for /L %%i in (1,1,10) do (
  timeout /t 1 /nobreak >nul
  curl -s http://127.0.0.1:8000/health >nul 2>&1
  if not errorlevel 1 goto ready
)
:ready

echo Services are ready.
echo.
echo Startup complete. The app should now be open in your browser.
