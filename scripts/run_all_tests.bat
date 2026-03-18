@echo off
REM ==========================================
REM 车载控制器测试数据分析系统 - 测试执行脚本
REM ==========================================

echo.
echo ==========================================
echo 车载控制器测试数据分析系统 - 测试执行
echo ==========================================
echo.

REM 设置项目根目录
set PROJECT_ROOT=%~dp0..
cd /d %PROJECT_ROOT%

echo 当前目录: %CD%
echo.

REM 创建测试报告目录
set REPORT_DIR=%PROJECT_ROOT%\test_reports
if not exist "%REPORT_DIR%" mkdir "%REPORT_DIR%"

REM 设置虚拟环境路径（如果使用虚拟环境）
set VENV_PATH=%PROJECT_ROOT%\venv

REM 激活虚拟环境（如果存在）
if exist "%VENV_PATH%\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call "%VENV_PATH%\Scripts\activate.bat"
    echo.
)

echo ==========================================
echo 步骤 1: 安装测试依赖
echo ==========================================
echo.
pip install pytest pytest-cov pytest-html pytest-xdist requests openpyxl scipy -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    exit /b 1
)
echo [完成] 依赖安装成功
echo.

echo ==========================================
echo 步骤 2: 运行代码风格检查（可选）
echo ==========================================
echo.
if exist "%PROJECT_ROOT%\backend\tests\__init__.py" (
    python -m flake8 %PROJECT_ROOT%\backend\app --count --select=E9,F63,F7,F82 --show-source --statistics
    if errorlevel 1 (
        echo [警告] 代码检查发现问题，但继续执行测试
    )
    echo.
) else (
    echo [跳过] 代码风格检查（flake8未安装或无源代码）
    echo.
)

echo ==========================================
echo 步骤 3: 运行单元测试
echo ==========================================
echo.
set UNIT_TEST_REPORT=%REPORT_DIR%\unit_test_report.html
set UNIT_TEST_COVERAGE=%REPORT_DIR%\unit_coverage.xml

cd /d %PROJECT_ROOT%\backend
pytest tests/ -m "not integration and not slow" -v --tb=short ^
    --html=%UNIT_TEST_REPORT% --self-contained-html ^
    --cov=app --cov-report=html:%REPORT_DIR%\coverage_html ^
    --cov-report=term-missing --cov-report=xml:%UNIT_TEST_COVERAGE%

if errorlevel 1 (
    echo [警告] 单元测试存在失败用例
    set UNIT_TEST_FAILED=1
) else (
    echo [完成] 单元测试全部通过
    set UNIT_TEST_FAILED=0
)
echo.

echo ==========================================
echo 步骤 4: 运行集成测试
echo ==========================================
echo.
set INTEGRATION_TEST_REPORT=%REPORT_DIR%\integration_test_report.html

cd /d %PROJECT_ROOT%\backend
pytest tests/ -m "integration" -v --tb=short ^
    --html=%INTEGRATION_TEST_REPORT% --self-contained-html ^
    -n auto

if errorlevel 1 (
    echo [警告] 集成测试存在失败用例
    set INTEGRATION_TEST_FAILED=1
) else (
    echo [完成] 集成测试全部通过
    set INTEGRATION_TEST_FAILED=0
)
echo.

echo ==========================================
echo 步骤 5: 运行慢速测试（可选）
echo ==========================================
echo.
echo 是否运行慢速测试？(Y/N)
set /p RUN_SLOW=
if /i "%RUN_SLOW%"=="Y" (
    echo 运行慢速测试...
    cd /d %PROJECT_ROOT%\backend
    pytest tests/ -m "slow" -v --tb=short
    echo.
) else (
    echo [跳过] 慢速测试已跳过
    echo.
)

echo ==========================================
echo 步骤 6: 生成测试汇总报告
echo ==========================================
echo.
set SUMMARY_REPORT=%REPORT_DIR%\test_summary.txt

(
    echo ==========================================
    echo 车载控制器测试数据分析系统 - 测试报告
    echo ==========================================
    echo.
    echo 测试日期: %date% %time%
    echo 项目路径: %PROJECT_ROOT%
    echo 报告目录: %REPORT_DIR%
    echo.
    echo ==========================================
    echo 测试结果汇总
    echo ==========================================
    echo.
    if %UNIT_TEST_FAILED%==0 (
        echo [通过] 单元测试
    ) else (
        echo [失败] 单元测试
    )
    if %INTEGRATION_TEST_FAILED%==0 (
        echo [通过] 集成测试
    ) else (
        echo [失败] 集成测试
    )
    echo.
    echo ==========================================
    echo 生成的报告文件
    echo ==========================================
    echo.
    echo - 单元测试报告: %UNIT_TEST_REPORT%
    echo - 集成测试报告: %INTEGRATION_TEST_REPORT%
    echo - 覆盖率报告: %REPORT_DIR%\coverage_html\index.html
    echo - 覆盖率XML: %UNIT_TEST_COVERAGE%
    echo.
    echo ==========================================
    echo 查看 HTML 报告
    echo ==========================================
    echo.
    echo 要查看HTML格式的测试报告，请打开以下文件:
    echo   %UNIT_TEST_REPORT%
    echo   %INTEGRATION_TEST_REPORT%
    echo.
) > %SUMMARY_REPORT%

type %SUMMARY_REPORT%

echo ==========================================
echo 测试执行完成
echo ==========================================
echo.
echo 所有测试报告已保存到: %REPORT_DIR%
echo.

REM 询问是否打开覆盖率报告
echo 是否打开覆盖率报告？(Y/N)
set /p OPEN_COVERAGE=
if /i "%OPEN_COVERAGE%"=="Y" (
    start "" "%REPORT_DIR%\coverage_html\index.html"
)

REM 返回错误码（如果有任何测试失败）
if %UNIT_TEST_FAILED%==1 exit /b 1
if %INTEGRATION_TEST_FAILED%==1 exit /b 1

exit /b 0
