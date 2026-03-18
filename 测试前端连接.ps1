# 测试前端连接

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试前端连接" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查前端服务状态
Write-Host "[检查] 检查前端服务状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri http://localhost:5173 -Method Head -TimeoutSec 5
    Write-Host "[成功] 前端服务正常响应" -ForegroundColor Green
    Write-Host "  状态码: $($response.StatusCode)" -ForegroundColor White
    Write-Host "  响应头 $($response.Headers['Content-Type'])" -ForegroundColor White
} catch {
    Write-Host "[失败] 前端服务无法访问" -ForegroundColor Red
    Write-Host "错误: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    
    # 检查端口是否占用
    Write-Host "[检查] 检查端口5173状态..." -ForegroundColor Yellow
    $portStatus = netstat -an | findstr :5173
    if ($portStatus) {
        Write-Host "端口5173状态: $portStatus" -ForegroundColor Green
    } else {
        Write-Host "端口5173未被占用" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "[建议] 请尝试以下操作：" -ForegroundColor Cyan
    Write-Host "1. 运行诊断脚本：诊断前端连接问题.bat" -ForegroundColor White
    Write-Host "2. 手动启动前端：启动前端服务.bat" -ForegroundColor White
    Write-Host "3. 重启系统后重新运行一键启动" -ForegroundColor White
    
    exit 1
}

Write-Host ""
Write-Host "[测试] 测试页面内容..." -ForegroundColor Yellow
try {
    $pageContent = Invoke-WebRequest -Uri http://localhost:5173 -TimeoutSec 5
    $title = ($pageContent.ParsedTitle -split '\n' | Where-Object { $_.Trim() } | Select-Object -First 1)
    
    Write-Host "[成功] 页面内容正常" -ForegroundColor Green
    Write-Host "页面标题: $title" -ForegroundColor White
    
    # 检查是否是React应用
    if ($pageContent.Content -match "React") {
        Write-Host "[信息] 检测到React应用" -ForegroundColor Green
    } else {
        Write-Host "[警告] 未检测到React应用" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "[失败] 获取页面内容失败" -ForegroundColor Red
    Write-Host "错误: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  测试完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "如果前端服务无法访问，请运行：" -ForegroundColor Yellow
Write-Host "1. 诊断前端连接问题.bat" -ForegroundColor White
Write-Host "2. 启动前端服务.bat" -ForegroundColor White
Write-Host ""
Read-Host "按任意键退出"