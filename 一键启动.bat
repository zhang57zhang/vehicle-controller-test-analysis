@echo off
chcp 936 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   Vehicle Controller Test Analysis
echo   One-Click Startup Script
echo ========================================
echo.

:: Check Python
echo [Check] Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Python not found, please install Python 3.9+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python is installed
echo.

:: Check Node.js
echo [Check] Checking Node.js environment...
node --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Node.js not found, please install Node.js 18+
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)
echo [OK] Node.js is installed
echo.

echo [Info] Environment check completed
echo.

:: Set directories
cd /d "%~dp0"
set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"

:: Check backend dependencies
echo [Check] Checking backend dependencies...
if not exist "%BACKEND_DIR%\venv\" (
    echo [Info] Backend virtual environment not found, creating...
    cd "%BACKEND_DIR%"
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd /d "%~dp0"
    echo [OK] Backend dependencies installed
) else (
    echo [OK] Backend virtual environment exists
)

:: Check frontend dependencies
echo [Check] Checking frontend dependencies...
if not exist "%FRONTEND_DIR%\node_modules\" (
    echo [Info] Frontend dependencies not found, installing...
    cd "%FRONTEND_DIR%"
    call npm install
    cd /d "%~dp0"
    echo [OK] Frontend dependencies installed
) else (
    echo [OK] Frontend dependencies exist
)

echo.

:: Start backend service
echo [Start] Starting backend service...
start "Backend Server" cmd /c "cd /d "%BACKEND_DIR%" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: Wait for backend service
echo [Wait] Waiting for backend service to start...
timeout /t 5 /nobreak >nul

:: Check backend service
curl -s http://localhost:8000/docs >nul 2>&1
if errorlevel 1 (
    echo [Warning] Backend service may not be running properly, check backend window
) else (
    echo [OK] Backend service started successfully
)

echo.

:: Start frontend service
echo [Start] Starting frontend service...
start "Frontend Server" cmd /c "cd /d "%FRONTEND_DIR%" && npm run dev"

:: Wait for frontend service
echo [Wait] Waiting for frontend service to start...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Services Started Successfully!
echo ========================================
echo.
echo   Backend API:  http://localhost:8000
echo   API Docs:     http://localhost:8000/api/docs
echo   Frontend Web: http://localhost:5173
echo.
echo   Tips:
echo   - Do not close these service windows
echo   - Press Ctrl+C in a window to stop that service
echo   - Run Stop-Service.bat to stop all services
echo.
pause
