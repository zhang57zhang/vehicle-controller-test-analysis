@echo off
chcp 65001 >nul

echo ========================================
echo   车载控制器测试数据分析系统
echo   停止服务脚本
echo ========================================
echo.

echo [停止] 正在查找并关闭服务...
echo.

:: 查找并关闭后端服务
echo [信息] 查找后端服务进程...
tasklist /FI "IMAGENAME eq python.exe" 2>nul | find /I /N "python.exe" >nul
if "%ERRORLEVEL%"=="0" (
    echo [停止] 发现后端服务进程，正在关闭...
    taskkill /F /FI "WINDOWTITLE eq 车载控制器测试-后端*" 2>nul
    timeout /t 1 /nobreak >nul
    taskkill /F /IM python.exe /FI "WINDOWTITLE eq 车载控制器测试-后端*" 2>nul
    echo [成功] 后端服务已关闭
) else (
    echo [信息] 未发现后端服务进程
)

echo.

:: 查找并关闭前端服务
echo [信息] 查找前端服务进程...
tasklist /FI "IMAGENAME eq node.exe" 2>nul | find /I /N "node.exe" >nul
if "%ERRORLEVEL%"=="0" (
    echo [停止] 发现前端服务进程，正在关闭...
    taskkill /F /FI "WINDOWTITLE eq 车载控制器测试-前端*" 2>nul
    timeout /t 1 /nobreak >nul
    taskkill /F /IM node.exe /FI "WINDOWTITLE eq 车载控制器测试-前端*" 2>nul
    echo [成功] 前端服务已关闭
) else (
    echo [信息] 未发现前端服务进程
)

echo.
echo ========================================
echo   ✅ 所有服务已停止
echo ========================================
echo.
pause
