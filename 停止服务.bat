@echo off
chcp 936 >nul
title 车载控制器测试数据分析系统 - 停止服务

echo ========================================
echo   车载控制器测试数据分析系统 - 停止服务
echo ========================================
echo.

echo [停止] 正在停止Node.js服务...
taskkill /F /IM node.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Node.js服务已停止
) else (
    echo [INFO] 未找到正在运行的Node.js进程
)

echo [停止] 正在停止Python服务...
taskkill /F /IM python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python服务已停止
) else (
    echo [INFO] 未找到正在运行的Python进程
)

:: 检查端口占用情况
echo.
echo [检查] 检查端口占用状态：
netstat -an | findstr :5173 >nul
if %errorlevel% equ 0 (
    echo [警告] 端口 5173 仍被占用，可能需要手动处理
    echo [建议] 手动打开任务管理器结束相关进程
) else (
    echo [OK] 端口 5173 已释放
)

netstat -an | findstr :8000 >nul
if %errorlevel% equ 0 (
    echo [警告] 端口 8000 仍被占用，可能需要手动处理
    echo [建议] 手动打开任务管理器结束相关进程
) else (
    echo [OK] 端口 8000 已释放
)

echo.
echo ========================================
echo   服务停止完成！
echo ========================================
echo.
echo [提示] 如需重新启动服务，请运行：
echo   双击运行：前端启动.bat
echo   双击运行：后端启动.bat
echo.
pause
