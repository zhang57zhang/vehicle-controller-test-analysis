@echo off
chcp 65001 >nul
title Frontend Launcher - Vehicle Test Analysis

echo ========================================
echo   Vehicle Controller Test Analysis
echo   Frontend Launcher (Fixed)
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
echo [Info] Working directory: %CD%
echo [Info] Executing: npx vite

:: 启动服务（在新的命令提示符窗口中）
start "Frontend Service" cmd /k "npx vite"

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
echo   4. Wait 10-20 seconds for service to fully start
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