@echo off
chcp 936 >nul

echo ========================================
echo   Vehicle Controller Test Analysis
echo   Stop Services Script
echo ========================================
echo.

echo [Info] Finding and stopping services...
echo.

:: Stop backend service
echo [Info] Checking backend service...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I /N "python.exe" >nul
if "%ERRORLEVEL%"=="0" (
    echo [Stop] Found backend service, stopping...
    taskkill /F /FI "WINDOWTITLE eq Backend Server*" 2>nul
    timeout /t 1 /nobreak >nul
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq Backend Server*" 2>nul
    echo [OK] Backend service stopped
) else (
    echo [Info] No backend service found
)

echo.

:: Stop frontend service
echo [Info] Checking frontend service...
tasklist /FI "IMAGENAME eq node.exe" 2>nul | find /I /N "node.exe" >nul
if "%ERRORLEVEL%"=="0" (
    echo [Stop] Found frontend service, stopping...
    taskkill /F /FI "WINDOWTITLE eq Frontend Server*" 2>nul
    timeout /t 1 /nobreak >nul
    taskkill /F /IM node.exe /FI "WINDOWTITLE eq Frontend Server*" 2>nul
    echo [OK] Frontend service stopped
) else (
    echo [Info] No frontend service found
)

echo.
echo ========================================
echo   All Services Stopped
echo ========================================
echo.
pause
