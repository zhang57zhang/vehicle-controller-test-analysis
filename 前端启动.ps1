# 车载控制器测试数据分析系统 - 简化启动脚本

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  网络连接简化启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设置目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $scriptDir "frontend"

# 检查并停止可能运行的服务
Write-Host "[检查] 停止现有服务..." -ForegroundColor Yellow
try {
    Stop-Process -Name "node" -Force -ErrorAction SilentlyContinue
    Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
    Write-Host "[OK] 已停止现有服务" -ForegroundColor Green
} catch {
    Write-Host "[WARNING] 无法停止某些进程" -ForegroundColor Yellow
}

Write-Host ""

# 启动前端服务
Write-Host "[启动] 启动前端服务..." -ForegroundColor Yellow
$frontendCmd = "cd $frontendDir; npm run dev"
Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $frontendCmd -WindowStyle Normal -Verb RunAs
Write-Host "[OK] 前端服务已启动" -ForegroundColor Green

# 等待服务启动
Write-Host "[等待] 等待前端服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请尝试以下地址：" -ForegroundColor Cyan
Write-Host ""
Write-Host "优先尝试（推荐）：" -ForegroundColor White
Write-Host "  http://localhost:5173" -ForegroundColor White
Write-Host "  http://127.0.0.1:5173" -ForegroundColor White
Write-Host ""
Write-Host "备用地址：" -ForegroundColor White
Write-Host "  http://192.168.1.100:5173" -ForegroundColor White
Write-Host "  http://192.168.6.1:5173" -ForegroundColor White
Write-Host "  http://192.168.200.1:5173" -ForegroundColor White
Write-Host ""
Write-Host "如果仍然无法访问，请运行：" -ForegroundColor Yellow
Write-Host "  双击运行：网络诊断.bat" -ForegroundColor White
Write-Host ""
Write-Host "常见解决方案：" -ForegroundColor White
Write-Host "1. 清除浏览器缓存：Ctrl+Shift+R" -ForegroundColor White
Write-Host "2. 使用 Chrome 或 Edge 浏览器" -ForegroundColor White
Write-Host "3. 检查防火墙是否阻止" -ForegroundColor White
Write-Host "4. 尝试手动输入地址" -ForegroundColor White
Write-Host ""
Write-Host "提示：服务将在新的命令提示符窗口中运行" -ForegroundColor Yellow
Write-Host "请勿关闭该窗口" -ForegroundColor Yellow
Write-Host ""
Read-Host "按任意键退出此窗口（服务将继续运行）"
