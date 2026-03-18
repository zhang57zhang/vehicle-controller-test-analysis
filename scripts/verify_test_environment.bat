@echo off
REM ==========================================
REM 测试环境验证脚本
REM ==========================================

echo.
echo ==========================================
echo 车载控制器测试数据分析系统
echo 测试环境验证
echo ==========================================
echo.

cd /d %~dp0..

set PROJECT_ROOT=%CD%
set BACKEND_DIR=%PROJECT_ROOT%\backend
set TESTS_DIR=%BACKEND_DIR%\tests
set TEST_DATA_DIR=%TESTS_DIR%\test_data
set SCRIPTS_DIR=%PROJECT_ROOT%\scripts

set ALL_CHECKS_PASSED=1

echo 检查项目结构...
echo.

REM 检查后端目录
if exist "%BACKEND_DIR%" (
    echo [OK] 后端目录存在
) else (
    echo [FAIL] 后端目录不存在
    set ALL_CHECKS_PASSED=0
)

REM 检查测试目录
if exist "%TESTS_DIR%" (
    echo [OK] 测试目录存在
) else (
    echo [FAIL] 测试目录不存在
    set ALL_CHECKS_PASSED=0
)

REM 检查测试数据目录
if exist "%TEST_DATA_DIR%" (
    echo [OK] 测试数据目录存在
) else (
    echo [FAIL] 测试数据目录不存在
    set ALL_CHECKS_PASSED=0
)

REM 检查脚本目录
if exist "%SCRIPTS_DIR%" (
    echo [OK] 脚本目录存在
) else (
    echo [FAIL] 脚本目录不存在
    set ALL_CHECKS_PASSED=0
)

echo.
echo 检查测试文件...
echo.

REM 检查测试配置文件
if exist "%TESTS_DIR%\conftest.py" (
    echo [OK] conftest.py 存在
) else (
    echo [FAIL] conftest.py 不存在
    set ALL_CHECKS_PASSED=0
)

if exist "%TESTS_DIR%\utils.py" (
    echo [OK] utils.py 存在
) else (
    echo [FAIL] utils.py 不存在
    set ALL_CHECKS_PASSED=0
)

if exist "%TESTS_DIR%\test_integration.py" (
    echo [OK] test_integration.py 存在
) else (
    echo [FAIL] test_integration.py 不存在
    set ALL_CHECKS_PASSED=0
)

echo.
echo 检查测试数据文件...
echo.

REM 检查测试数据文件
if exist "%TEST_DATA_DIR%\sample.dbc" (
    echo [OK] sample.dbc 存在
) else (
    echo [FAIL] sample.dbc 不存在
    set ALL_CHECKS_PASSED=0
)

if exist "%TEST_DATA_DIR%\sample.csv" (
    echo [OK] sample.csv 存在
) else (
    echo [FAIL] sample.csv 不存在
    set ALL_CHECKS_PASSED=0
)

if exist "%TEST_DATA_DIR%\sample.log" (
    echo [OK] sample.log 存在
) else (
    echo [FAIL] sample.log 不存在
    set ALL_CHECKS_PASSED=0
)

if exist "%TEST_DATA_DIR%\sample.xlsx" (
    echo [OK] sample.xlsx 存在
) else (
    echo [WARN] sample.xlsx 不存在（将由Python脚本生成）
)

if exist "%TEST_DATA_DIR%\generate_test_data.py" (
    echo [OK] generate_test_data.py 存在
) else (
    echo [WARN] generate_test_data.py 不存在
)

REM 检查MATLAB文件（警告级别）
if exist "%TEST_DATA_DIR%\sample_v6.mat" (
    echo [OK] sample_v6.mat 存在
) else (
    echo [WARN] sample_v6.mat 不存在（需要运行生成脚本）
)

if exist "%TEST_DATA_DIR%\sample_v73.mat" (
    echo [OK] sample_v73.mat 存在
) else (
    echo [WARN] sample_v73.mat 不存在（需要运行生成脚本）
)

echo.
echo 检查脚本文件...
echo.

if exist "%SCRIPTS_DIR%\run_all_tests.bat" (
    echo [OK] run_all_tests.bat 存在
) else (
    echo [FAIL] run_all_tests.bat 不存在
    set ALL_CHECKS_PASSED=0
)

if exist "%SCRIPTS_DIR%\run_all_tests.sh" (
    echo [OK] run_all_tests.sh 存在
) else (
    echo [WARN] run_all_tests.sh 不存在（Linux/macOS）
)

echo.
echo 检查文档文件...
echo.

if exist "%PROJECT_ROOT%\tests\README.md" (
    echo [OK] tests/README.md 存在
) else (
    echo [WARN] tests/README.md 不存在
)

if exist "%PROJECT_ROOT%\tests\acceptance_test_cases.md" (
    echo [OK] tests/acceptance_test_cases.md 存在
) else (
    echo [FAIL] tests/acceptance_test_cases.md 不存在
    set ALL_CHECKS_PASSED=0
)

if exist "%PROJECT_ROOT%\.github\workflows\test.yml" (
    echo [OK] .github/workflows/test.yml 存在
) else (
    echo [FAIL] .github/workflows/test.yml 不存在
    set ALL_CHECKS_PASSED=0
)

echo.
echo 检查Python环境...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python未安装或不在PATH中
    set ALL_CHECKS_PASSED=0
) else (
    python --version
    echo [OK] Python已安装
)

python -c "import pytest" >nul 2>&1
if errorlevel 1 (
    echo [WARN] pytest未安装
    echo       运行: pip install pytest pytest-cov pytest-html
) else (
    echo [OK] pytest已安装
    python -c "import pytest; print(f'  pytest版本: {pytest.__version__}')"
)

python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [WARN] FastAPI未安装
    echo       运行: cd backend ^&^& pip install -r requirements.txt
) else (
    echo [OK] FastAPI已安装
    python -c "import fastapi; print(f'  FastAPI版本: {fastapi.__version__}')"
)

python -c "import pandas" >nul 2>&1
if errorlevel 1 (
    echo [WARN] pandas未安装
    echo       运行: pip install pandas
) else (
    echo [OK] pandas已安装
    python -c "import pandas; print(f'  pandas版本: {pandas.__version__}')"
)

python -c "import openpyxl" >nul 2>&1
if errorlevel 1 (
    echo [WARN] openpyxl未安装（Excel支持需要）
    echo       运行: pip install openpyxl
) else (
    echo [OK] openpyxl已安装
    python -c "import openpyxl; print(f'  openpyxl版本: {openpyxl.__version__}')"
)

python -c "import scipy" >nul 2>&1
if errorlevel 1 (
    echo [WARN] scipy未安装（MATLAB支持需要）
    echo       运行: pip install scipy h5py
) else (
    echo [OK] scipy已安装
    python -c "import scipy; print(f'  scipy版本: {scipy.__version__}')"
)

python -c "import cantools" >nul 2>&1
if errorlevel 1 (
    echo [WARN] cantools未安装（DBC解析需要）
    echo       运行: pip install cantools
) else (
    echo [OK] cantools已安装
)

echo.
echo ==========================================
echo 验证结果
echo ==========================================
echo.

if %ALL_CHECKS_PASSED%==1 (
    echo [成功] 所有关键检查通过！
    echo.
    echo 可以开始运行测试：
    echo   scripts\run_all_tests.bat
    echo.
    exit /b 0
) else (
    echo [警告] 部分检查未通过
    echo.
    echo 请解决上述问题后再运行测试
    echo.
    exit /b 1
)
