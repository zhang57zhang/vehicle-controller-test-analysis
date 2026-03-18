#!/bin/bash

# ==========================================
# 车载控制器测试数据分析系统 - 测试执行脚本
# ==========================================

set -e  # 遇到错误立即退出

echo ""
echo "=========================================="
echo "车载控制器测试数据分析系统 - 测试执行"
echo "=========================================="
echo ""

# 获取脚本所在目录的父目录（项目根目录）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "当前目录: $(pwd)"
echo ""

# 创建测试报告目录
REPORT_DIR="$PROJECT_ROOT/test_reports"
mkdir -p "$REPORT_DIR"

# 设置虚拟环境路径（如果使用虚拟环境）
VENV_PATH="$PROJECT_ROOT/venv"

# 激活虚拟环境（如果存在）
if [ -f "$VENV_PATH/bin/activate" ]; then
    echo "激活虚拟环境..."
    source "$VENV_PATH/bin/activate"
    echo ""
fi

echo "=========================================="
echo "步骤 1: 安装测试依赖"
echo "=========================================="
echo ""

pip install pytest pytest-cov pytest-html pytest-xdist requests openpyxl scipy -q

echo "[完成] 依赖安装成功"
echo ""

echo "=========================================="
echo "步骤 2: 运行代码风格检查（可选）"
echo "=========================================="
echo ""

if [ -f "$PROJECT_ROOT/backend/tests/__init__.py" ]; then
    if command -v flake8 &> /dev/null; then
        flake8 "$PROJECT_ROOT/backend/app" --count --select=E9,F63,F7,F82 --show-source --statistics || true
        echo "[完成] 代码风格检查完成"
    else
        echo "[跳过] flake8未安装"
    fi
else
    echo "[跳过] 未找到源代码"
fi

echo ""

echo "=========================================="
echo "步骤 3: 运行单元测试"
echo "=========================================="
echo ""

UNIT_TEST_REPORT="$REPORT_DIR/unit_test_report.html"
UNIT_TEST_COVERAGE="$REPORT_DIR/unit_coverage.xml"

cd "$PROJECT_ROOT/backend"

pytest tests/ -m "not integration and not slow" -v --tb=short \
    --html="$UNIT_TEST_REPORT" --self-contained-html \
    --cov=app --cov-report=html:"$REPORT_DIR/coverage_html" \
    --cov-report=term-missing --cov-report=xml:"$UNIT_TEST_COVERAGE" \
    || UNIT_TEST_FAILED=1

if [ -z "$UNIT_TEST_FAILED" ]; then
    echo "[完成] 单元测试全部通过"
    UNIT_TEST_FAILED=0
else
    echo "[警告] 单元测试存在失败用例"
fi

echo ""

echo "=========================================="
echo "步骤 4: 运行集成测试"
echo "=========================================="
echo ""

INTEGRATION_TEST_REPORT="$REPORT_DIR/integration_test_report.html"

pytest tests/ -m "integration" -v --tb=short \
    --html="$INTEGRATION_TEST_REPORT" --self-contained-html \
    -n auto \
    || INTEGRATION_TEST_FAILED=1

if [ -z "$INTEGRATION_TEST_FAILED" ]; then
    echo "[完成] 集成测试全部通过"
    INTEGRATION_TEST_FAILED=0
else
    echo "[警告] 集成测试存在失败用例"
fi

echo ""

echo "=========================================="
echo "步骤 5: 运行慢速测试（可选）"
echo "=========================================="
echo ""

read -p "是否运行慢速测试？(Y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "运行慢速测试..."
    pytest tests/ -m "slow" -v --tb=short || true
    echo ""
else
    echo "[跳过] 慢速测试已跳过"
    echo ""
fi

echo "=========================================="
echo "步骤 6: 生成测试汇总报告"
echo "=========================================="
echo ""

SUMMARY_REPORT="$REPORT_DIR/test_summary.txt"

cat > "$SUMMARY_REPORT" << EOF
=========================================
车载控制器测试数据分析系统 - 测试报告
=========================================

测试日期: $(date '+%Y-%m-%d %H:%M:%S')
项目路径: $PROJECT_ROOT
报告目录: $REPORT_DIR

=========================================
测试结果汇总
=========================================

EOF

if [ $UNIT_TEST_FAILED -eq 0 ]; then
    echo "[通过] 单元测试" >> "$SUMMARY_REPORT"
else
    echo "[失败] 单元测试" >> "$SUMMARY_REPORT"
fi

if [ $INTEGRATION_TEST_FAILED -eq 0 ]; then
    echo "[通过] 集成测试" >> "$SUMMARY_REPORT"
else
    echo "[失败] 集成测试" >> "$SUMMARY_REPORT"
fi

cat >> "$SUMMARY_REPORT" << EOF

=========================================
生成的报告文件
=========================================

- 单元测试报告: $UNIT_TEST_REPORT
- 集成测试报告: $INTEGRATION_TEST_REPORT
- 覆盖率报告: $REPORT_DIR/coverage_html/index.html
- 覆盖率XML: $UNIT_TEST_COVERAGE

=========================================
查看 HTML 报告
=========================================

要查看HTML格式的测试报告，请打开以下文件:
  $UNIT_TEST_REPORT
  $INTEGRATION_TEST_REPORT

EOF

cat "$SUMMARY_REPORT"

echo "=========================================="
echo "测试执行完成"
echo "=========================================="
echo ""
echo "所有测试报告已保存到: $REPORT_DIR"
echo ""

# 询问是否打开覆盖率报告（仅在支持的操作系统上）
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    read -p "是否打开覆盖率报告？(Y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v xdg-open &> /dev/null; then
            xdg-open "$REPORT_DIR/coverage_html/index.html"
        elif command -v open &> /dev/null; then
            open "$REPORT_DIR/coverage_html/index.html"
        else
            echo "无法自动打开浏览器，请手动打开: $REPORT_DIR/coverage_html/index.html"
        fi
    fi
fi

# 返回错误码（如果有任何测试失败）
exit $((UNIT_TEST_FAILED + INTEGRATION_TEST_FAILED))
