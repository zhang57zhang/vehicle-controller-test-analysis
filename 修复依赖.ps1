# 车载控制器测试数据分析系统 - 修复依赖问题

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  修复依赖问题" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 设置目录
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptDir "backend"

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

Write-Host ""

# 进入backend目录
Write-Host "[信息] 进入backend目录" -ForegroundColor Yellow
Push-Location $backendDir

# 检查虚拟环境
Write-Host "[检查] 检查虚拟环境..." -ForegroundColor Yellow
$venvPath = Join-Path $backendDir "venv"

# 删除旧的虚拟环境
if (Test-Path $venvPath) {
    Write-Host "[信息] 发现旧的虚拟环境，正在删除..." -ForegroundColor Yellow
    Remove-Item -Path $venvPath -Recurse -Force
    Write-Host "[成功] 旧的虚拟环境已删除" -ForegroundColor Green
}

# 创建新的虚拟环境
Write-Host "[信息] 创建新的虚拟环境..." -ForegroundColor Yellow
python -m venv venv
Write-Host "[成功] 虚拟环境创建完成" -ForegroundColor Green

Write-Host ""

# 激活虚拟环境
Write-Host "[激活] 激活虚拟环境..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
& $activateScript

# 检查当前Python
Write-Host "[检查] 检查虚拟环境中的Python..." -ForegroundColor Yellow
$currentPython = python --version 2>&1
$currentPythonPath = where.exe python
Write-Host "[信息] 当前Python版本: $currentPython" -ForegroundColor Green
Write-Host "[信息] 当前Python路径: $currentPythonPath" -ForegroundColor Green

Write-Host ""

# 升级pip
Write-Host "[升级] 升级pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "[成功] pip升级完成" -ForegroundColor Green

Write-Host ""

# 安装依赖
Write-Host "[安装] 安装后端依赖..." -ForegroundColor Yellow
Write-Host "[提示] 这可能需要几分钟，请耐心等待..." -ForegroundColor Cyan

try {
    pip install -r requirements.txt
    Write-Host "[成功] 依赖安装完成" -ForegroundColor Green
} catch {
    Write-Host "[错误] 依赖安装失败" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Pop-Location
    Read-Host "按任意键退出"
    exit 1
}

Write-Host ""

# 验证关键包
Write-Host "[验证] 验证关键包是否安装..." -ForegroundColor Yellow

$packages = @("pydantic-settings", "fastapi", "uvicorn", "sqlalchemy", "pandas")

foreach ($pkg in $packages) {
    try {
        $result = python -c "import $pkg; print($pkg.__version__)" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] $pkg 已安装 (版本: $result)" -ForegroundColor Green
        } else {
            Write-Host "[警告] $pkg 可能未正确安装" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "[错误] $pkg 安装失败" -ForegroundColor Red
    }
}

Write-Host ""

# 返回原目录
Pop-Location

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  依赖修复完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  现在可以运行一键启动脚本启动系统了" -ForegroundColor Yellow
Write-Host ""
Write-Host "  推荐启动方式：" -ForegroundColor Cyan
Write-Host "  - 双击运行: 一键启动_新版.bat" -ForegroundColor White
Write-Host "  - 备用方式: 一键启动.bat" -ForegroundColor White
Write-Host ""
Read-Host "按任意键退出"
