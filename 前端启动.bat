@echo off
chcp 65001 >nul
title Frontend Launcher - Vehicle Test Analysis

echo ========================================
echo   Vehicle Controller Test Analysis
echo   Frontend Launcher
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set FRONTEND_DIR=%SCRIPT_DIR%frontend

echo [Checking] Stopping existing services...
taskkill /F /IM node.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1
echo [OK] Services cleared

echo.

if not exist "%FRONTEND_DIR%" (
    echo [ERROR] Frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\package.json" (
    echo [WARNING] package.json not found
    if not exist "%FRONTEND_DIR%\node_modules" (
        echo [Installing] Installing dependencies...
        cd /d "%FRONTEND_DIR%"
        npm install
        echo.
    )
)

echo [Starting] Launching frontend service...
cd /d "%FRONTEND_DIR%"
start "Frontend Service" cmd /c "npm run dev"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Frontend Started Successfully
echo ========================================
echo.
echo Access URLs:
echo   Primary: http://localhost:5173
echo   Alternative: http://127.0.0.1:5173
echo.
echo If not accessible, try:
echo   1. Clear browser cache: Ctrl+Shift+R
echo   2. Use Chrome or Edge browser
echo   3. Check firewall settings
echo.
echo The service is running in a new window.
echo Do not close that window for service to continue.
echo.
timeout /t 5 /nobreak >nul

netstat -an | findstr :5173 >nul
if %errorlevel% equ 0 (
    echo [OK] Frontend service running on port 5173
) else (
    echo [WARNING] Service not detected on port 5173
    echo [CHECK] Please check console output for errors
)

echo.
pause
