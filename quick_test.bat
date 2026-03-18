@echo off
chcp 65001 >nul
title Frontend Test

echo ========================================
echo   Frontend Service Test
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set FRONTEND_DIR=%SCRIPT_DIR%frontend

echo [Test 1] Checking frontend directory...
if exist "%FRONTEND_DIR%" (
    echo [OK] Frontend directory exists
) else (
    echo [ERROR] Frontend directory not found
    pause
    exit /b 1
)

echo [Test 2] Checking package.json...
if exist "%FRONTEND_DIR%\package.json" (
    echo [OK] package.json exists
) else (
    echo [ERROR] package.json not found
    pause
    exit /b 1
)

echo [Test 3] Testing vite command...
cd /d "%FRONTEND_DIR%"
npx vite --version
echo.
echo [Test 4] Starting frontend service...
echo [Starting] Frontend service will start in new window
start "Frontend Service" cmd /k "npx vite"

echo.
echo ========================================
echo   Test Complete!
echo ========================================
echo.
echo Frontend service is starting...
echo Access: http://localhost:5173
echo.
pause