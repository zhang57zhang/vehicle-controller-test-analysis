# ==========================================
# 车载控制器测试数据分析系统
# 测试环境验证脚本 (PowerShell)
# ==========================================

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "车载控制器测试数据分析系统" -ForegroundColor Cyan
Write-Host "测试环境验证" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$BACKEND_DIR = Join-Path $PROJECT_ROOT "backend"
$TESTS_DIR = Join-Path $BACKEND_DIR "tests"
$TEST_DATA_DIR = Join-Path $TESTS_DIR "test_data"
$SCRIPTS_DIR = Join-Path $PROJECT_ROOT "scripts"

$ALL_CHECKS_PASSED = $true

Write-Host "检查项目结构..." -ForegroundColor Yellow
Write-Host ""

# 检查后端目录
if (Test-Path $BACKEND_DIR) {
    Write-Host "[OK] 后端目录存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] 后端目录不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

# 检查测试目录
if (Test-Path $TESTS_DIR) {
    Write-Host "[OK] 测试目录存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] 测试目录不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

# 检查测试数据目录
if (Test-Path $TEST_DATA_DIR) {
    Write-Host "[OK] 测试数据目录存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] 测试数据目录不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

# 检查脚本目录
if (Test-Path $SCRIPTS_DIR) {
    Write-Host "[OK] 脚本目录存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] 脚本目录不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

Write-Host ""
Write-Host "检查测试文件..." -ForegroundColor Yellow
Write-Host ""

# 检查测试配置文件
$conftestPath = Join-Path $TESTS_DIR "conftest.py"
if (Test-Path $conftestPath) {
    Write-Host "[OK] conftest.py 存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] conftest.py 不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

$utilsPath = Join-Path $TESTS_DIR "utils.py"
if (Test-Path $utilsPath) {
    Write-Host "[OK] utils.py 存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] utils.py 不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

$integrationPath = Join-Path $TESTS_DIR "test_integration.py"
if (Test-Path $integrationPath) {
    Write-Host "[OK] test_integration.py 存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] test_integration.py 不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

Write-Host ""
Write-Host "检查测试数据文件..." -ForegroundColor Yellow
Write-Host ""

# 检查测试数据文件
$dbcPath = Join-Path $TEST_DATA_DIR "sample.dbc"
if (Test-Path $dbcPath) {
    Write-Host "[OK] sample.dbc 存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] sample.dbc 不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

$csvPath = Join-Path $TEST_DATA_DIR "sample.csv"
if (Test-Path $csvPath) {
    Write-Host "[OK] sample.csv 存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] sample.csv 不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

$logPath = Join-Path $TEST_DATA_DIR "sample.log"
if (Test-Path $logPath) {
    Write-Host "[OK] sample.log 存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] sample.log 不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

$xlsxPath = Join-Path $TEST_DATA_DIR "sample.xlsx"
if (Test-Path $xlsxPath) {
    Write-Host "[OK] sample.xlsx 存在" -ForegroundColor Green
} else {
    Write-Host "[WARN] sample.xlsx 不存在（将由Python脚本生成）" -ForegroundColor Yellow
}

$genScriptPath = Join-Path $TEST_DATA_DIR "generate_test_data.py"
if (Test-Path $genScriptPath) {
    Write-Host "[OK] generate_test_data.py 存在" -ForegroundColor Green
} else {
    Write-Host "[WARN] generate_test_data.py 不存在" -ForegroundColor Yellow
}

# 检查MATLAB文件（警告级别）
$mat6Path = Join-Path $TEST_DATA_DIR "sample_v6.mat"
if (Test-Path $mat6Path) {
    Write-Host "[OK] sample_v6.mat 存在" -ForegroundColor Green
} else {
    Write-Host "[WARN] sample_v6.mat 不存在（需要运行生成脚本）" -ForegroundColor Yellow
}

$mat73Path = Join-Path $TEST_DATA_DIR "sample_v73.mat"
if (Test-Path $mat73Path) {
    Write-Host "[OK] sample_v73.mat 存在" -ForegroundColor Green
} else {
    Write-Host "[WARN] sample_v73.mat 不存在（需要运行生成脚本）" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "检查脚本文件..." -ForegroundColor Yellow
Write-Host ""

$batPath = Join-Path $SCRIPTS_DIR "run_all_tests.bat"
if (Test-Path $batPath) {
    Write-Host "[OK] run_all_tests.bat 存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] run_all_tests.bat 不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

$shPath = Join-Path $SCRIPTS_DIR "run_all_tests.sh"
if (Test-Path $shPath) {
    Write-Host "[OK] run_all_tests.sh 存在" -ForegroundColor Green
} else {
    Write-Host "[WARN] run_all_tests.sh 不存在（Linux/macOS）" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "检查文档文件..." -ForegroundColor Yellow
Write-Host ""

$testsReadmePath = Join-Path $PROJECT_ROOT "tests\README.md"
if (Test-Path $testsReadmePath) {
    Write-Host "[OK] tests/README.md 存在" -ForegroundColor Green
} else {
    Write-Host "[WARN] tests/README.md 不存在" -ForegroundColor Yellow
}

$acceptancePath = Join-Path $PROJECT_ROOT "tests\acceptance_test_cases.md"
if (Test-Path $acceptancePath) {
    Write-Host "[OK] tests/acceptance_test_cases.md 存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] tests/acceptance_test_cases.md 不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

$ciPath = Join-Path $PROJECT_ROOT ".github\workflows\test.yml"
if (Test-Path $ciPath) {
    Write-Host "[OK] .github/workflows/test.yml 存在" -ForegroundColor Green
} else {
    Write-Host "[FAIL] .github/workflows/test.yml 不存在" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

Write-Host ""
Write-Host "检查Python环境..." -ForegroundColor Yellow
Write-Host ""

try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python已安装: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] Python未安装或不在PATH中" -ForegroundColor Red
    $ALL_CHECKS_PASSED = $false
}

try {
    $pytestVersion = python -c "import pytest; print(pytest.__version__)" 2>&1
    Write-Host "[OK] pytest已安装 (版本: $pytestVersion)" -ForegroundColor Green
} catch {
    Write-Host "[WARN] pytest未安装" -ForegroundColor Yellow
    Write-Host "      运行: pip install pytest pytest-cov pytest-html" -ForegroundColor Gray
}

try {
    $fastapiVersion = python -c "import fastapi; print(fastapi.__version__)" 2>&1
    Write-Host "[OK] FastAPI已安装 (版本: $fastapiVersion)" -ForegroundColor Green
} catch {
    Write-Host "[WARN] FastAPI未安装" -ForegroundColor Yellow
    Write-Host "      运行: cd backend; pip install -r requirements.txt" -ForegroundColor Gray
}

try {
    $pandasVersion = python -c "import pandas; print(pandas.__version__)" 2>&1
    Write-Host "[OK] pandas已安装 (版本: $pandasVersion)" -ForegroundColor Green
} catch {
    Write-Host "[WARN] pandas未安装" -ForegroundColor Yellow
    Write-Host "      运行: pip install pandas" -ForegroundColor Gray
}

try {
    $openpyxlVersion = python -c "import openpyxl; print(openpyxl.__version__)" 2>&1
    Write-Host "[OK] openpyxl已安装 (版本: $openpyxlVersion)" -ForegroundColor Green
} catch {
    Write-Host "[WARN] openpyxl未安装（Excel支持需要）" -ForegroundColor Yellow
    Write-Host "      运行: pip install openpyxl" -ForegroundColor Gray
}

try {
    $scipyVersion = python -c "import scipy; print(scipy.__version__)" 2>&1
    Write-Host "[OK] scipy已安装 (版本: $scipyVersion)" -ForegroundColor Green
} catch {
    Write-Host "[WARN] scipy未安装（MATLAB支持需要）" -ForegroundColor Yellow
    Write-Host "      运行: pip install scipy h5py" -ForegroundColor Gray
}

try {
    $cantoolsVersion = python -c "import cantools; print(cantools.__version__)" 2>&1
    Write-Host "[OK] cantools已安装 (版本: $cantoolsVersion)" -ForegroundColor Green
} catch {
    Write-Host "[WARN] cantools未安装（DBC解析需要）" -ForegroundColor Yellow
    Write-Host "      运行: pip install cantools" -ForegroundColor Gray
}

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "验证结果" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

if ($ALL_CHECKS_PASSED) {
    Write-Host "[成功] 所有关键检查通过！" -ForegroundColor Green
    Write-Host ""
    Write-Host "可以开始运行测试：" -ForegroundColor Cyan
    Write-Host "  scripts\run_all_tests.bat" -ForegroundColor Yellow
    Write-Host ""
    exit 0
} else {
    Write-Host "[警告] 部分检查未通过" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "请解决上述问题后再运行测试" -ForegroundColor Cyan
    Write-Host ""
    exit 1
}
