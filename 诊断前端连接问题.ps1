# 诊断和修复前端连接问题

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  诊断前端连接问题" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendDir = Join-Path $scriptDir "frontend"
$backendDir = Join-Path $scriptDir "backend"

# 检查端口占用
Write-Host "[检查] 检查端口占用情况..." -ForegroundColor Yellow
try {
    $frontendPort5173 = netstat -an | findstr :5173
    if ($frontendPort5173) {
        Write-Host "[信息] 前端端口5173状态:" -ForegroundColor Green
        Write-Host "  $frontendPort5173" -ForegroundColor White
    } else {
        Write-Host "[警告] 端口5173未被占用，前端服务可能未启动" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[错误] 检查端口状态失败" -ForegroundColor Red
}

try {
    $backendPort8000 = netstat -an | findstr :8000
    if ($backendPort8000) {
        Write-Host "[信息] 后端端口8000状态:" -ForegroundColor Green
        Write-Host "  $backendPort8000" -ForegroundColor White
    } else {
        Write-Host "[警告] 端口8000未被占用，后端服务可能未启动" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[错误] 检查端口状态失败" -ForegroundColor Red
}

Write-Host ""

# 测试连接
Write-Host "[测试] 测试前端连接..." -ForegroundColor Yellow
try {
    $frontendResponse = Invoke-WebRequest -Uri http://localhost:5173 -Method Head -TimeoutSec 5
    Write-Host "[成功] 前端服务正常响应 (HTTP $($frontendResponse.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "[失败] 前端连接失败: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

Write-Host "[测试] 测试后端连接..." -ForegroundColor Yellow
try {
    $backendResponse = Invoke-WebRequest -Uri http://localhost:8000/api/projects -Method Head -TimeoutSec 5
    Write-Host "[成功] 后端服务正常响应 (HTTP $($backendResponse.StatusCode))" -ForegroundColor Green
} catch {
    $errorMsg = $_.Exception.Message
    if ($errorMsg -match "405.*Method Not Allowed") {
        Write-Host "[信息] 后端服务运行正常 (GET方法不被允许)" -ForegroundColor Yellow
    } else {
        Write-Host "[失败] 后端连接失败: $errorMsg" -ForegroundColor Red
    }
}

Write-Host ""

# 检查进程
Write-Host "[检查] 检查运行进程..." -ForegroundColor Yellow
$frontendProcesses = Get-Process | Where-Object { $_.ProcessName -match "(vite|node)" -and $_.Id -ne $PID }
if ($frontendProcesses) {
    Write-Host "[信息] 发现前端相关进程:" -ForegroundColor Green
    foreach ($proc in $frontendProcesses) {
        Write-Host "  $($proc.ProcessName) - ID: $($proc.Id)" -ForegroundColor White
    }
} else {
    Write-Host "[警告] 未发现前端相关进程" -ForegroundColor Yellow
}

Write-Host ""

# 检查前端目录结构
Write-Host "[检查] 检查前端目录结构..." -ForegroundColor Yellow
if (Test-Path $frontendDir) {
    Write-Host "[信息] 前端目录存在: $frontendDir" -ForegroundColor Green
    
    # 检查关键文件
    $files = @("package.json", "vite.config.ts", "src/main.tsx", "src/App.tsx")
    foreach ($file in $files) {
        $filePath = Join-Path $frontendDir $file
        if (Test-Path $filePath) {
            Write-Host "[OK] $file 存在" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] $file 不存在" -ForegroundColor Red
        }
    }
} else {
    Write-Host "[ERROR] 前端目录不存在: $frontendDir" -ForegroundColor Red
}

Write-Host ""

# 停止所有相关服务
Write-Host "[清理] 停止相关服务..." -ForegroundColor Yellow
$frontendWindowTitle = "Frontend Server"
$backendWindowTitle = "Backend Server"

# 停止后端服务
$backendProcesses = Get-Process | Where-Object { $_.ProcessName -eq "python" }
foreach ($proc in $backendProcesses) {
    if ($proc.MainWindowTitle -match $backendWindowTitle) {
        Write-Host "[停止] 停止后端服务 (ID: $($proc.Id))" -ForegroundColor Yellow
        Stop-Process -Id $proc.Id -Force
    }
}

# 停止前端服务
$frontendNodeProcesses = Get-Process | Where-Object { $_.ProcessName -eq "node" }
foreach ($proc in $frontendNodeProcesses) {
    if ($proc.MainWindowTitle -match $frontendWindowTitle) {
        Write-Host "[停止] 停止前端服务 (ID: $($proc.Id))" -ForegroundColor Yellow
        Stop-Process -Id $proc.Id -Force
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  诊断完成，准备重新启动服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "下一步建议：" -ForegroundColor Yellow
Write-Host "1. 手动检查前后端服务是否启动" -ForegroundColor White
Write-Host "2. 手动重新启动前端服务" -ForegroundColor White
Write-Host "3. 检查浏览器控制台错误信息" -ForegroundColor White
Write-Host "4. 检查端口是否被其他程序占用" -ForegroundColor White

Write-Host ""
Read-Host "按任意键退出"
