# 启动前端服务（修复连接问题）

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  启动前端服务（修复版本）" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设置目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $scriptDir "frontend"

Write-Host "[检查] 检查前端目录..." -ForegroundColor Yellow
if (-not (Test-Path $frontendDir)) {
    Write-Host "[错误] 前端目录不存在: $frontendDir" -ForegroundColor Red
    exit 1
}

Write-Host "[信息] 前端目录存在: $frontendDir" -ForegroundColor Green

# 检查node_modules
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "[信息] 前端依赖未安装，正在安装..." -ForegroundColor Yellow
    Push-Location $frontendDir
    npm install
    Pop-Location
    Write-Host "[成功] 依赖安装完成" -ForegroundColor Green
}

Write-Host ""

# 停止现有的前端服务
Write-Host "[清理] 停止现有服务..." -ForegroundColor Yellow
Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue | Out-Null
Stop-Process -Name "vite" -Force -ErrorAction SilentlyContinue | Out-Null
Write-Host "[信息] 已停止现有服务" -ForegroundColor Green

Write-Host ""

# 切换到前端目录
Write-Host "[切换] 进入前端目录..." -ForegroundColor Yellow
Push-Location $frontendDir

# 设置环境变量
$env:PORT = "5173"
$env:HOST = "0.0.0.0"

Write-Host "[启动] 启动前端开发服务器..." -ForegroundColor Yellow
Write-Host "端口: 5173" -ForegroundColor White
Write-Host "主机: 0.0.0.0" -ForegroundColor White
Write-Host "路径: $(pwd)" -ForegroundColor White
Write-Host ""

# 启动前端服务
try {
    # 使用npm run dev启动
    npm run dev
} catch {
    Write-Host "[错误] 前端服务启动失败" -ForegroundColor Red
    Write-Host "错误信息: $($_.Exception.Message)" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  前端服务启动完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "访问地址:" -ForegroundColor Cyan
Write-Host "  http://localhost:5173" -ForegroundColor White
Write-Host "  http://127.0.0.1:5173" -ForegroundColor White
Write-Host ""
Write-Host "按 Ctrl+C 停止服务" -ForegroundColor Yellow
Write-Host ""
Pause