@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   车载控制器测试数据分析系统
echo   一键启动脚本
echo ========================================
echo.

:: 检查是否已经安装Python和Node.js
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Node.js，请先安装Node.js 18+
    pause
    exit /b 1
)

echo [检查] Python和Node.js环境正常
echo.

:: 设置目录
cd /d "%~dp0"
set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"

:: 检查依赖是否安装
echo [检查] 后端依赖...
if not exist "%BACKEND_DIR%\venv\" (
    echo [信息] 后端虚拟环境不存在，正在创建...
    cd "%BACKEND_DIR%"
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    cd /d "%~dp0"
) else (
    echo [信息] 后端虚拟环境已存在
)

echo [检查] 前端依赖...
if not exist "%FRONTEND_DIR%\node_modules\" (
    echo [信息] 前端依赖未安装，正在安装...
    cd "%FRONTEND_DIR%"
    call npm install
    cd /d "%~dp0"
) else (
    echo [信息] 前端依赖已安装
)

echo.

:: 创建启动状态文件
set "STATUS_FILE=%~dp0.starting_status"
echo false > "%STATUS_FILE%"

:: 启动后端服务（新窗口）
echo [启动] 后端服务...
start "车载控制器测试-后端" cmd /c "cd /d "%BACKEND_DIR%" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: 等待后端服务启动
echo [等待] 后端服务启动中...
timeout /t 5 /nobreak >nul

:: 检查后端服务是否启动成功
curl -s http://localhost:8000/docs >nul 2>&1
if errorlevel 1 (
    echo [警告] 后端服务可能未正常启动，请检查后端窗口
) else (
    echo [成功] 后端服务启动成功
)

echo.

:: 启动前端服务（新窗口）
echo [启动] 前端服务...
start "车载控制器测试-前端" cmd /c "cd /d "%FRONTEND_DIR%" && npm run dev"

:: 等待前端服务启动
echo [等待] 前端服务启动中...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   ✅ 服务启动完成！
echo ========================================
echo.
echo   📊 后端服务：http://localhost:8000
echo   📝 API文档：  http://localhost:8000/api/docs
echo   🌐 前端服务：http://localhost:5173
echo.
echo   提示：
echo   - 请勿关闭这两个服务窗口
echo   - 按 Ctrl+C 可以停止对应窗口中的服务
echo   - 如需停止所有服务，请使用"停止服务.bat"
echo.
pause
