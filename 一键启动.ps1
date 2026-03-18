# 车载控制器测试数据分析系统 - 一键启动脚本（PowerShell版本）

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  车载控制器测试数据分析系统" -ForegroundColor Cyan
Write-Host "  一键启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python
Write-Host "[检查] 检查Python环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[信息] Python版本: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到Python，请先安装Python 3.9+" -ForegroundColor Red
    Write-Host "下载地址: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "按任意键退出"
    exit 1
}

# 检查Node.js
Write-Host "[检查] 检查Node.js环境..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "[信息] Node.js版本: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "[错误] 未检测到Node.js，请先安装Node.js 18+" -ForegroundColor Red
    Write-Host "下载地址: https://nodejs.org/" -ForegroundColor Yellow
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "[成功] 环境检查完成" -ForegroundColor Green
Write-Host ""

# 设置目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"
$frontendDir = Join-Path $scriptDir "frontend"

# 检查后端依赖
Write-Host "[检查] 后端依赖..." -ForegroundColor Yellow
$venvPath = Join-Path $backendDir "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[信息] 后端虚拟环境不存在，正在创建..." -ForegroundColor Yellow
    Push-Location $backendDir
    python -m venv venv
    & (Join-Path $venvPath "Scripts\Activate.ps1")
    pip install -r requirements.txt
    Pop-Location
    Write-Host "[成功] 后端依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "[信息] 后端虚拟环境已存在" -ForegroundColor Green
}

# 检查前端依赖
Write-Host "[检查] 前端依赖..." -ForegroundColor Yellow
$nodeModulesPath = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $nodeModulesPath)) {
    Write-Host "[信息] 前端依赖未安装，正在安装..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
    Write-Host "[成功] 前端依赖安装完成" -ForegroundColor Green
} else {
    Write-Host "[信息] 前端依赖已安装" -ForegroundColor Green
}

Write-Host ""

# 启动后端服务
Write-Host "[启动] 后端服务..." -ForegroundColor Yellow
$backendCmd = "cd $backendDir; venv\Scripts\activate.bat; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $backendCmd -WindowStyle Normal -Verb RunAs
Write-Host "[信息] 后端服务已在后台启动" -ForegroundColor Green

# 等待后端服务启动
Write-Host "[等待] 后端服务启动中..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 检查后端服务
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 2
    Write-Host "[成功] 后端服务启动成功" -ForegroundColor Green
} catch {
    Write-Host "[警告] 后端服务可能未正常启动，请检查后端窗口" -ForegroundColor Yellow
}

Write-Host ""

# 启动前端服务
Write-Host "[启动] 前端服务..." -ForegroundColor Yellow
$frontendCmd = "cd $frontendDir; npm run dev"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $frontendCmd -WindowStyle Normal -Verb RunAs
Write-Host "[信息] 前端服务已在后台启动" -ForegroundColor Green

# 等待前端服务启动
Write-Host "[等待] 前端服务启动中..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 检查前端服务
Write-Host "[检查] 检查前端服务..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 3
    Write-Host "[成功] 前端服务启动成功" -ForegroundColor Green
} catch {
    Write-Host "[警告] 前端服务可能未正常启动，请检查前端窗口" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  服务启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  后端服务： http://localhost:8000" -ForegroundColor Cyan
Write-Host "  API文档：  http://localhost:8000/api/docs" -ForegroundColor Cyan
Write-Host "  前端服务： http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "  提示：" -ForegroundColor Yellow
Write-Host "  - 请勿关闭这两个服务窗口" -ForegroundColor White
Write-Host "  - 按 Ctrl+C 可以停止对应窗口中的服务" -ForegroundColor White
Write-Host "  - 如需停止所有服务，请运行 停止服务.bat" -ForegroundColor White
Write-Host ""
Read-Host "按任意键关闭此窗口（服务将继续运行）"
