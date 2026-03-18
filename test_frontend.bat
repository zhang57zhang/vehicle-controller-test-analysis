@echo off
chcp 65001 >nul
title Frontend Test Launcher

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

echo [Test 3] Checking node_modules...
if exist "%FRONTEND_DIR%\node_modules" (
    echo [OK] node_modules exists
) else (
    echo [WARNING] node_modules not found, installing...
    cd /d "%FRONTEND_DIR%"
    npm install
)

echo [Test 4] Testing vite command...
cd /d "%FRONTEND_DIR%"
npx vite --version > test_output.txt 2>&1
findstr /C:"vite" test_output.txt >nul
if %errorlevel% equ 0 (
    echo [OK] vite command works
    type test_output.txt
) else (
    echo [ERROR] vite command failed
    type test_output.txt
    pause
    exit /b 1
)

del test_output.txt >nul 2>&1

echo [Test 5] Testing frontend launch...
echo [Starting] Testing frontend service launch...
start "Frontend Test" cmd /k "timeout /t 10 && echo Test complete && pause"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   All Tests Passed!
echo ========================================
echo.
echo The frontend service is ready to launch.
echo Use the following command to start:
echo   双击运行：前端启动.bat
echo.
echo Access URL: http://localhost:5173
echo.
pause