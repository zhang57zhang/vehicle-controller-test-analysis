# 车载控制器测试数据分析系统 - 网络连接问题诊断

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  网络连接问题诊断" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设置目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $scriptDir "frontend"

Write-Host "[检查] 检查服务状态..." -ForegroundColor Yellow

# 检查端口占用
Write-Host "[1] 检查端口5173状态..." -ForegroundColor Yellow
try {
    $connection = Test-NetConnection -ComputerName localhost -Port 5173 -WarningAction SilentlyContinue
    if ($connection.TcpTestSucceeded) {
        Write-Host "[OK] 端口5173可访问" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] 端口5173不可访问" -ForegroundColor Red
    }
} catch {
    Write-Host "[ERROR] 无法测试端口连接" -ForegroundColor Red
}

Write-Host ""

# 检查前端服务进程
Write-Host "[2] 检查前端服务进程..." -ForegroundColor Yellow
try {
    $processes = Get-Process node -ErrorAction SilentlyContinue | Where-Object {$_.ProcessName -eq "node"}
    if ($processes) {
        Write-Host "[OK] 发现Node.js进程" -ForegroundColor Green
        $processes | ForEach-Object {
            Write-Host "  进程ID: $($_.Id), 内存: $([math]::Round($_.WorkingSet/1MB, 2)) MB"
        }
    } else {
        Write-Host "[ERROR] 未发现Node.js进程" -ForegroundColor Red
    }
} catch {
    Write-Host "[ERROR] 无法检查进程" -ForegroundColor Red
}

Write-Host ""

# 检查本地访问
Write-Host "[3] 测试本地访问..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri http://localhost:5173 -UserAgent "Mozilla/5.0" -TimeoutSec 5 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] http://localhost:5173 正常访问" -ForegroundColor Green
        Write-Host "  响应大小: $($response.ContentLength) 字节"
        Write-Host "  内容类型: $($response.ContentType)"
    } else {
        Write-Host "[ERROR] http://localhost:5173 返回错误: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "[ERROR] 无法访问 http://localhost:5173" -ForegroundColor Red
    Write-Host "  错误信息: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# 检查网络访问
Write-Host "[4] 测试网络访问..." -ForegroundColor Yellow
$interfaces = @(
    @{Name="Ethernet"; IP="192.168.1.100"},
    @{Name="VMnet1"; IP="192.168.6.1"},
    @{Name="VMnet8"; IP="192.168.200.1"}
)

foreach ($interface in $interfaces) {
    try {
        $response = Invoke-WebRequest -Uri "http://$($interface.IP):5173" -UserAgent "Mozilla/5.0" -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "[OK] http://$($interface.IP):5173 正常访问 ($($interface.Name))" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] http://$($interface.IP):5173 返回错误: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[ERROR] 无法访问 http://$($interface.IP):5173 ($($interface.Name))" -ForegroundColor Yellow
    }
}

Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  问题诊断完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "解决方案：" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 清除浏览器缓存：" -ForegroundColor White
Write-Host "   - 按 Ctrl+Shift+R (强制刷新)" -ForegroundColor White
Write-Host "   - 或按 F12 -> Network -> 清空缓存" -ForegroundColor White
Write-Host ""
Write-Host "2. 检查浏览器设置：" -ForegroundColor White
Write-Host "   - 确保没有阻止 localhost 访问" -ForegroundColor White
Write-Host "   - 尝试使用 Chrome 或 Edge" -ForegroundColor White
Write-Host ""
Write-Host "3. 检查防火墙：" -ForegroundColor White
Write-Host "   - 确保 Node.js 允许通过防火墙" -ForegroundColor White
Write-Host "   - 临时关闭防火墙测试" -ForegroundColor White
Write-Host ""
Write-Host "4. 检查代理设置：" -ForegroundColor White
Write-Host "   - 确保 browser 没有代理设置" -ForegroundColor White
Write-Host ""
Write-Host "5. 重启前端服务：" -ForegroundColor White
Write-Host "   - 双击 停止服务.bat" -ForegroundColor White
Write-Host "   - 双击 一键启动_新版.bat" -ForegroundColor White
Write-Host ""
Read-Host "按任意键退出"
