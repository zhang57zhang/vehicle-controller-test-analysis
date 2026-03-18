"""
简化的单元测试：DBC和MAT文件解析器

只测试核心功能，不涉及复杂的DBC格式。
"""
import pytest
import numpy as np
from scipy import io as sio

from app.services.mat_parser import MatParser, FileFormatError, MatParserError


# ==================== 测试MAT解析器 ====================

class TestMatParserSimple:
    """MAT解析器简化测试"""

    def test_mat_parser_init_valid_file(self, tmp_path):
        """测试使用有效文件初始化MAT解析器"""
        # 创建测试数据
        time_data = np.arange(0, 10, 0.1).reshape(-1, 1)
        signal1 = np.sin(time_data * 2 * np.pi)
        signal2 = np.cos(time_data * 2 * np.pi)

        mat_data = {
            'time': time_data,
            'signal1': signal1,
            'signal2': signal2,
            'scalar': 42
        }

        mat_file = tmp_path / "test.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        assert parser.mat_file_path.name == "test.mat"
        assert parser.data is None

    def test_mat_parser_load_file(self, tmp_path):
        """测试加载MAT文件"""
        mat_data = {
            'time': np.arange(10),
            'signal': np.sin(np.arange(10))
        }

        mat_file = tmp_path / "test.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        assert parser.data is not None
        assert 'time' in parser.data
        assert 'signal' in parser.data

    def test_mat_parser_get_variable(self, tmp_path):
        """测试获取变量"""
        mat_data = {
            'time': np.arange(10),
            'value': 42.5
        }

        mat_file = tmp_path / "test.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        time_data = parser.get_variable('time')
        assert time_data is not None

        value = parser.get_variable('value')
        assert value == 42.5

    def test_mat_parser_get_metadata(self, tmp_path):
        """测试获取元数据"""
        mat_data = {
            'time': np.arange(10),
            'signal': np.arange(10)
        }

        mat_file = tmp_path / "test.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        metadata = parser.get_metadata()
        assert 'file_name' in metadata
        assert 'version' in metadata
        assert 'variable_names' in metadata
        assert len(metadata['variable_names']) == 2

    def test_mat_parser_get_summary(self, tmp_path):
        """测试获取摘要信息"""
        mat_data = {
            'time': np.arange(10),
            'signal': np.arange(10)
        }

        mat_file = tmp_path / "test.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        summary = parser.get_summary()
        assert 'file_name' in summary
        assert 'variable_count' in summary
        assert summary['variable_count'] >= 2

    def test_mat_parser_error_before_load(self, tmp_path):
        """测试在加载前调用方法"""
        mat_file = tmp_path / "test.mat"
        mat_file.write_text("dummy")

        parser = MatParser(str(mat_file))

        with pytest.raises(MatParserError):
            parser.get_variable('time')

        with pytest.raises(MatParserError):
            parser.get_metadata()

    def test_mat_file_without_time_series(self, tmp_path):
        """测试没有时序数据的MAT文件"""
        mat_data = {
            'data1': np.array([1, 2, 3]),
            'data2': np.array([4, 5, 6])
        }

        mat_file = tmp_path / "no_time.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        time_series = parser.get_time_series_data()
        assert time_series is None

    def test_empty_mat_file(self, tmp_path):
        """测试空MAT文件"""
        mat_data = {}

        mat_file = tmp_path / "empty.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        metadata = parser.get_metadata()
        assert metadata['variable_count'] == 0
        assert metadata['variable_names'] == []

    def test_mat_file_large_arrays(self, tmp_path):
        """测试处理大型数组"""
        large_array = np.random.rand(1000, 100)
        time_array = np.arange(1000)

        mat_data = {
            'large_array': large_array,
            'time': time_array
        }

        mat_file = tmp_path / "large.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        summary = parser.get_summary()
        assert summary['variable_count'] >= 1


# ==================== 便捷函数测试 ====================

from app.services.mat_parser import parse_mat_file

def test_parse_mat_file_convenience_function(tmp_path):
    """测试便捷函数parse_mat_file"""
    mat_data = {
        'time': np.arange(10),
        'signal': np.arange(10)
    }

    mat_file = tmp_path / "test.mat"
    sio.savemat(str(mat_file), mat_data)

    summary = parse_mat_file(str(mat_file))

    assert 'file_name' in summary
    assert 'version' in summary
    assert 'variable_count' in summary
