# 测试指南

本文档提供车载控制器测试数据分析系统的测试执行指南。

## 目录结构

```
tests/
├── README.md                           # 本文件
├── acceptance_test_cases.md            # 合格性测试用例文档
└── ...
```

```
backend/tests/
├── __init__.py                         # 测试包初始化
├── conftest.py                         # pytest配置和fixtures
├── utils.py                            # 测试工具函数
├── test_integration.py                 # 集成测试
└── test_data/                          # 测试数据目录
    ├── sample.dbc                      # DBC测试文件
    ├── sample.csv                      # CSV测试文件
    ├── sample.log                      # CAN log测试文件
    ├── generate_test_data.py           # 测试数据生成脚本
    └── MATLAB_FILE_INFO.md             # MATLAB文件说明
```

```
scripts/
├── run_all_tests.bat                   # Windows测试脚本
└── run_all_tests.sh                    # Linux/macOS测试脚本
```

```
.github/workflows/
└── test.yml                            # CI/CD配置
```

## 快速开始

### 1. 安装测试依赖

```bash
cd backend
pip install pytest pytest-cov pytest-html pytest-xdist requests openpyxl scipy
```

### 2. 运行所有测试

**Windows:**
```cmd
cd ..
scripts\run_all_tests.bat
```

**Linux/macOS:**
```bash
cd ..
chmod +x scripts/run_all_tests.sh
./scripts/run_all_tests.sh
```

### 3. 查看测试报告

测试完成后，HTML格式的报告将保存在 `test_reports/` 目录下：
- `unit_test_report.html` - 单元测试报告
- `integration_test_report.html` - 集成测试报告
- `coverage_html/index.html` - 代码覆盖率报告

## 运行特定测试

### 运行单元测试

```bash
cd backend
pytest tests/ -m "not integration" -v
```

### 运行集成测试

```bash
cd backend
pytest tests/ -m "integration" -v
```

### 运行特定标记的测试

```bash
cd backend
pytest tests/ -m "dbc" -v      # DBC相关测试
pytest tests/ -m "matlab" -v   # MATLAB相关测试
```

### 运行特定测试文件

```bash
cd backend
pytest tests/test_integration.py -v
```

### 运行特定测试函数

```bash
cd backend
pytest tests/test_integration.py::test_complete_file_upload_flow -v
```

## 测试覆盖率

### 生成覆盖率报告

```bash
cd backend
pytest tests/ --cov=app --cov-report=html
```

### 查看覆盖率报告

打开 `backend/htmlcov/index.html` 在浏览器中查看详细覆盖率报告。

### 设置覆盖率阈值

在 `conftest.py` 或命令行中设置：

```bash
pytest tests/ --cov=app --cov-fail-under=70
```

## 测试数据

### 准备MATLAB测试文件

MATLAB文件需要特殊工具生成：

```bash
cd backend/tests/test_data
python generate_test_data.py
```

这将生成：
- `sample_v6.mat` - MATLAB v6格式
- `sample_v73.mat` - MATLAB v7.3格式

要求：
- scipy（用于MATLAB v6）
- h5py（用于MATLAB v7.3）

### 创建自定义测试数据

使用 `utils.py` 中的工具函数：

```python
from utils import create_sample_csv
from pathlib import Path

create_sample_csv(Path("custom_test.csv"), num_rows=100)
```

## 持续集成

### CI/CD 工作流

项目使用 GitHub Actions 进行持续集成：

**触发条件:**
- 推送到 `main` 或 `develop` 分支
- 创建 Pull Request
- 手动触发

**工作流包含:**
1. 代码风格检查（Flake8, Black, isort）
2. 单元测试（多操作系统、多Python版本）
3. 集成测试
4. 性能测试（仅在main分支）
5. 安全扫描（Bandit, Safety）
6. 测试报告生成

**查看CI状态:**
GitHub仓库 → Actions 标签

### 本地模拟CI

```bash
# 代码风格检查
flake8 backend/app
black --check backend/app
isort --check-only backend/app

# 运行测试
pytest backend/tests/ -v

# 安全扫描
bandit -r backend/app
safety check
```

## 测试标记

| 标记 | 说明 | 示例 |
|------|------|------|
| `integration` | 集成测试 | `test_complete_file_upload_flow` |
| `unit` | 单元测试 | `test_file_upload` |
| `slow` | 慢速测试 | `test_performance_large_file` |
| `dbc` | DBC相关 | `test_dbc_upload_and_parsing` |
| `matlab` | MATLAB相关 | `test_matlab_import` |

## 编写测试

### 测试文件命名规范

- 单元测试: `test_<module>.py`
- 集成测试: `test_integration.py`
- 性能测试: `test_performance.py`

### 测试函数命名规范

使用描述性名称，以 `test_` 开头：

```python
def test_file_upload_success():
    pass

def test_dbc_parse_with_invalid_file():
    pass
```

### 使用 Fixtures

```python
from conftest import client, test_db, test_data_dir

def test_with_fixtures(client, test_data_dir):
    csv_path = test_data_dir / "sample.csv"
    response = client.post("/api/files/upload", ...)
    assert response.status_code == 200
```

### 添加文档字符串

```python
def test_file_upload(client, test_data_dir):
    """
    Test file upload functionality

    Steps:
    1. Upload CSV file
    2. Verify response
    3. Check file metadata
    """
    pass
```

## 故障排查

### 常见问题

**1. 导入错误:**
```bash
ModuleNotFoundError: No module named 'app'
```
**解决:** 确保在 `backend/` 目录下运行测试

**2. 测试数据库锁定:**
```bash
Database is locked
```
**解决:** 删除 `backend/test.db` 文件

**3. 文件上传失败:**
```bash
FileNotFoundError
```
**解决:** 确保测试数据文件存在于 `backend/tests/test_data/`

**4. 覆盖率报告为空:**
```bash
No data to report
```
**解决:** 确保 `--cov=app` 指向正确的模块

## 最佳实践

1. **保持测试独立性** - 每个测试应该独立运行，不依赖其他测试
2. **使用fixtures** - 复用测试数据清理逻辑
3. **添加有意义的断言** - 使用描述性错误消息
4. **测试边界条件** - 不仅测试正常路径，也要测试异常情况
5. **保持测试快速** - 将慢速测试标记为 `@pytest.mark.slow`
6. **定期更新测试** - 随着功能更新，同步更新测试

## 贡献指南

提交代码前，请确保：

1. ✅ 所有测试通过
2. ✅ 代码覆盖率不降低
3. ✅ 遵循代码风格规范
4. ✅ 添加相应的测试用例
5. ✅ 更新文档（如有必要）

## 参考资料

- [Pytest文档](https://docs.pytest.org/)
- [pytest-cov文档](https://pytest-cov.readthedocs.io/)
- [FastAPI测试指南](https://fastapi.tiangolo.com/tutorial/testing/)
- [合格性测试用例](./acceptance_test_cases.md)

## 支持

如有问题或建议，请：
1. 查看项目文档
2. 搜索已有的Issues
3. 创建新的Issue并提供详细信息
