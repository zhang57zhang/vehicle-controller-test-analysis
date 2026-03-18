"""
Pytest配置和共享fixtures

提供测试配置、数据库设置和其他共享功能。
"""
import pytest
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def test_data_dir():
    """测试数据目录fixture"""
    data_dir = project_root / "tests" / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir


# ==================== 测试运行钩子 ====================

def pytest_configure(config):
    """Pytest配置钩子"""
    # 添加自定义标记
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "parser: marks tests as parser tests")
    config.addinivalue_line("markers", "api: marks tests as API tests")


def pytest_collection_modifyitems(config, items):
    """修改测试收集项"""
    # 默认跳过慢速测试，除非特别指定
    if not config.getoption("--runslow"):
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="run integration tests"
    )
