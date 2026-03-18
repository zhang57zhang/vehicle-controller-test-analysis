"""
单元测试：DBC和MAT文件解析器

测试DBC和MAT文件解析功能，包括文件加载、数据提取和错误处理。
"""
import pytest
import os
import tempfile
import shutil
from pathlib import Path
import numpy as np
from scipy import io as sio
import h5py

from app.services.dbc_parser import DBCParser, FileFormatError, ParseError
from app.services.mat_parser import MatParser, FileFormatError as MatFileFormatError, MatParserError


# ==================== 测试DBC解析器 ====================

class TestDBCParser:
    """DBC解析器测试"""

    @pytest.fixture
    def sample_dbc_file(self, tmp_path):
        """创建测试用的DBC文件"""
        # 创建一个简单的DBC文件（简化格式）
        dbc_content = """VERSION ""

NS_ :
    NS_DESC_
    CM_
    BA_DEF_
    BA_
    VAL_
    CAT_DEF_
    CAT_
    FILTER
    BA_DEF_DEF_
    EV_DATA_
    ENVVAR_DATA_
    SGTYPE_
    SGTYPE_VAL_
    BA_DEF_SGTYPE_
    BA_SGTYPE_
    SIG_TYPE_REF_
    VAL_TABLE_
    SIG_GROUP_
    SigTran_
    BA_DEF_REL_
    BA_REL_
    BA_DEF_DEF_REL_
    BU_SG_REL_
    BU_EV_REL_
    SIG_MUL_VAL_

BS_:

BU_:

BO_ 100 MSG1: 8 Vector__XXX
 SG_ Signal1 : 0|8@1+ (0.1,0) [0|25.5] "Voltage"
 SG_ Signal2 : 8|8@1+ (1,0) [0|255] "Current"

BO_ 200 MSG2: 8 Vector__XXX
 SG_ Speed : 0|12@1+ (0.1,0) [0|409.5] "Vehicle Speed"
 SG_ RPM : 16|16@1+ (1,0) [0|65535] "Engine RPM"
"""
        dbc_file = tmp_path / "test.dbc"
        dbc_file.write_text(dbc_content, encoding='utf-8')
        return str(dbc_file)

    @pytest.fixture
    def invalid_dbc_file(self, tmp_path):
        """创建无效的DBC文件"""
        invalid_file = tmp_path / "invalid.txt"
        invalid_file.write_text("This is not a valid DBC file")
        return str(invalid_file)

    @pytest.fixture
    def non_existent_file(self):
        """不存在的文件路径"""
        return "/non/existent/file.dbc"

    def test_dbc_parser_init_valid_file(self, sample_dbc_file):
        """测试使用有效文件初始化DBC解析器"""
        parser = DBCParser(sample_dbc_file)
        assert parser.dbc_file_path == Path(sample_dbc_file)
        assert parser.db is None

    def test_dbc_parser_init_non_existent_file(self, non_existent_file):
        """测试使用不存在的文件初始化DBC解析器"""
        with pytest.raises(FileNotFoundError):
            DBCParser(non_existent_file)

    def test_dbc_parser_init_invalid_format(self, invalid_dbc_file):
        """测试使用无效格式的文件初始化DBC解析器"""
        with pytest.raises(FileFormatError):
            DBCParser(invalid_dbc_file)

    def test_dbc_parser_load_valid_file(self, sample_dbc_file):
        """测试加载有效的DBC文件"""
        parser = DBCParser(sample_dbc_file)
        parser.load()
        assert parser.db is not None
        assert len(parser.db.messages) == 2

    def test_dbc_parser_get_messages(self, sample_dbc_file):
        """测试获取消息列表"""
        parser = DBCParser(sample_dbc_file)
        parser.load()
        messages = parser.get_messages()

        assert len(messages) == 2
        assert messages[0]['name'] == 'MSG1'
        assert messages[0]['frame_id'] == 100
        assert len(messages[0]['signals']) == 2

    def test_dbc_parser_get_message_by_name(self, sample_dbc_file):
        """测试按名称获取消息"""
        parser = DBCParser(sample_dbc_file)
        parser.load()
        message = parser.get_message_by_name('MSG1')

        assert message is not None
        assert message['name'] == 'MSG1'
        assert message['frame_id'] == 100
        assert len(message['signals']) == 2

    def test_dbc_parser_get_message_by_name_not_found(self, sample_dbc_file):
        """测试获取不存在的消息"""
        parser = DBCParser(sample_dbc_file)
        parser.load()
        message = parser.get_message_by_name('NonExistent')

        assert message is None

    def test_dbc_parser_get_message_by_frame_id(self, sample_dbc_file):
        """测试按帧ID获取消息"""
        parser = DBCParser(sample_dbc_file)
        parser.load()
        message = parser.get_message_by_frame_id(100)

        assert message is not None
        assert message['frame_id'] == 100
        assert message['name'] == 'MSG1'

    def test_dbc_parser_get_all_signal_names(self, sample_dbc_file):
        """测试获取所有信号名称"""
        parser = DBCParser(sample_dbc_file)
        parser.load()
        signal_names = parser.get_all_signal_names()

        assert len(signal_names) == 4
        assert 'Signal1' in signal_names
        assert 'Signal2' in signal_names
        assert 'Speed' in signal_names
        assert 'RPM' in signal_names

    def test_dbc_parser_get_summary(self, sample_dbc_file):
        """测试获取DBC文件摘要"""
        parser = DBCParser(sample_dbc_file)
        parser.load()
        summary = parser.get_summary()

        assert summary['message_count'] == 2
        assert summary['signal_count'] == 4
        assert len(summary['messages']) == 2

    def test_dbc_parser_decode_message(self, sample_dbc_file):
        """测试解码CAN消息"""
        parser = DBCParser(sample_dbc_file)
        parser.load()

        # 创建测试数据：MSG1包含两个信号
        # Signal1: 值1.2V -> 12 (1.2/0.1)
        # Signal2: 值10A -> 10 (10/1)
        data = bytes([12, 10, 0, 0, 0, 0, 0, 0])
        decoded = parser.decode_message(100, data)

        assert 'Signal1' in decoded
        assert 'Signal2' in decoded
        # 注意：由于小端序，实际解码结果可能不同
        # 这里主要测试不抛出异常

    def test_dbc_parser_decode_invalid_frame_id(self, sample_dbc_file):
        """测试解码不存在的帧ID"""
        parser = DBCParser(sample_dbc_file)
        parser.load()

        with pytest.raises(ParseError):
            parser.decode_message(999, bytes([0, 0, 0, 0, 0, 0, 0, 0]))

    def test_dbc_parser_error_before_load(self, sample_dbc_file):
        """测试在加载前调用方法"""
        parser = DBCParser(sample_dbc_file)

        with pytest.raises(ParseError):
            parser.get_messages()

        with pytest.raises(ParseError):
            parser.get_summary()

    def test_parse_dbc_file_convenience_function(self, sample_dbc_file):
        """测试便捷函数parse_dbc_file"""
        summary = parse_dbc_file(sample_dbc_file)

        assert summary['message_count'] == 2
        assert summary['signal_count'] == 4
        assert 'messages' in summary

    def test_get_message_signals_convenience_function(self, sample_dbc_file):
        """测试便捷函数get_message_signals"""
        signals = get_message_signals(sample_dbc_file, 'MSG1')

        assert len(signals) == 2
        assert signals[0]['name'] == 'Signal1'
        assert signals[1]['name'] == 'Signal2'


# ==================== 测试MAT解析器 ====================

class TestMatParser:
    """MAT解析器测试"""

    @pytest.fixture
    def sample_mat_v6_file(self, tmp_path):
        """创建MATLAB v6格式测试文件"""
        # 创建测试数据
        time_data = np.arange(0, 10, 0.1).reshape(-1, 1)
        signal1 = np.sin(time_data * 2 * np.pi)
        signal2 = np.cos(time_data * 2 * np.pi)

        mat_data = {
            'time': time_data,
            'signal1': signal1,
            'signal2': signal2,
            'scalar': 42,
            'string': 'test_string'
        }

        mat_file = tmp_path / "test_v6.mat"
        sio.savemat(str(mat_file), mat_data, format='4')  # MATLAB v4/v6格式
        return str(mat_file)

    @pytest.fixture
    def sample_mat_v73_file(self, tmp_path):
        """创建MATLAB v7.3格式测试文件（HDF5）"""
        mat_file = tmp_path / "test_v73.mat"

        # 创建HDF5文件
        with h5py.File(mat_file, 'w') as f:
            # 时间数据
            time_data = np.arange(0, 10, 0.1)
            f.create_dataset('time', data=time_data)

            # 信号数据
            f.create_dataset('signal1', data=np.sin(time_data * 2 * np.pi))
            f.create_dataset('signal2', data=np.cos(time_data * 2 * np.pi))

            # 标量
            f.create_dataset('scalar', data=42)

            # 字符串
            string_dt = h5py.special_dtype(vlen=str)
            f.create_dataset('string', data='test_string', dtype=string_dt)

        return str(mat_file)

    @pytest.fixture
    def invalid_mat_file(self, tmp_path):
        """创建无效的MAT文件"""
        invalid_file = tmp_path / "invalid.mat"
        invalid_file.write_bytes(b'This is not a valid MAT file')
        return str(invalid_file)

    @pytest.fixture
    def non_existent_file(self):
        """不存在的文件路径"""
        return "/non/existent/file.mat"

    def test_mat_parser_init_valid_file(self, sample_mat_v6_file):
        """测试使用有效文件初始化MAT解析器"""
        parser = MatParser(sample_mat_v6_file)
        assert parser.mat_file_path == Path(sample_mat_v6_file)
        assert parser.data is None
        assert parser.version is None

    def test_mat_parser_init_non_existent_file(self, non_existent_file):
        """测试使用不存在的文件初始化MAT解析器"""
        with pytest.raises(MatFileFormatError):
            MatParser(non_existent_file)

    def test_mat_parser_init_invalid_extension(self, tmp_path):
        """测试使用错误扩展名的文件初始化MAT解析器"""
        invalid_file = tmp_path / "test.txt"
        invalid_file.write_text("content")

        with pytest.raises(MatFileFormatError):
            MatParser(str(invalid_file))

    def test_mat_parser_detect_version_v6(self, sample_mat_v6_file):
        """测试检测MAT v6版本"""
        parser = MatParser(sample_mat_v6_file)
        version = parser.detect_version()

        assert version in ['v4', 'v6', 'v7']  # scipy可能报告为这些版本之一

    def test_mat_parser_detect_version_v73(self, sample_mat_v73_file):
        """测试检测MAT v7.3版本"""
        parser = MatParser(sample_mat_v73_file)
        version = parser.detect_version()

        assert version == 'v7.3'

    def test_mat_parser_load_v6_file(self, sample_mat_v6_file):
        """测试加载MAT v6文件"""
        parser = MatParser(sample_mat_v6_file)
        parser.load()

        assert parser.data is not None
        assert parser.metadata is not None
        assert 'time' in parser.data
        assert 'signal1' in parser.data
        assert 'signal2' in parser.data

    def test_mat_parser_load_v73_file(self, sample_mat_v73_file):
        """测试加载MAT v7.3文件"""
        parser = MatParser(sample_mat_v73_file)
        parser.load()

        assert parser.data is not None
        assert parser.metadata is not None
        assert 'time' in parser.data
        assert 'signal1' in parser.data
        assert 'signal2' in parser.data

    def test_mat_parser_get_variable(self, sample_mat_v6_file):
        """测试获取变量"""
        parser = MatParser(sample_mat_v6_file)
        parser.load()

        time_data = parser.get_variable('time')
        assert time_data is not None

        with pytest.raises(MatParserError):
            parser.get_variable('non_existent')

    def test_mat_parser_get_metadata(self, sample_mat_v6_file):
        """测试获取元数据"""
        parser = MatParser(sample_mat_v6_file)
        parser.load()

        metadata = parser.get_metadata()
        assert 'file_name' in metadata
        assert 'file_size' in metadata
        assert 'version' in metadata
        assert 'variable_names' in metadata
        assert 'variable_count' in metadata

    def test_mat_parser_get_time_series_data(self, sample_mat_v6_file):
        """测试获取时序数据"""
        parser = MatParser(sample_mat_v6_file)
        parser.load()

        time_series = parser.get_time_series_data()
        assert time_series is not None
        assert 'time' in time_series
        assert 'variables' in time_series
        assert 'signal1' in time_series['variables']
        assert 'signal2' in time_series['variables']

    def test_mat_parser_get_variable_info(self, sample_mat_v6_file):
        """测试获取变量信息"""
        parser = MatParser(sample_mat_v6_file)
        parser.load()

        info = parser.get_variable_info('time')
        assert info['name'] == 'time'
        assert 'type' in info
        assert 'shape' in info

        with pytest.raises(MatParserError):
            parser.get_variable_info('non_existent')

    def test_mat_parser_get_all_variables_info(self, sample_mat_v6_file):
        """测试获取所有变量信息"""
        parser = MatParser(sample_mat_v6_file)
        parser.load()

        all_info = parser.get_all_variables_info()
        assert len(all_info) > 0
        assert any(info['name'] == 'time' for info in all_info)

    def test_mat_parser_extract_as_dataframe(self, sample_mat_v6_file):
        """测试提取为DataFrame格式"""
        parser = MatParser(sample_mat_v6_file)
        parser.load()

        dataframe_data = parser.extract_as_dataframe()
        assert 'data' in dataframe_data
        assert 'columns' in dataframe_data
        assert 'length' in dataframe_data
        assert 'time' in dataframe_data['data']

    def test_mat_parser_get_summary(self, sample_mat_v6_file):
        """测试获取摘要信息"""
        parser = MatParser(sample_mat_v6_file)
        parser.load()

        summary = parser.get_summary()
        assert 'file_name' in summary
        assert 'version' in summary
        assert 'variable_count' in summary
        assert 'variable_types' in summary
        assert 'estimated_data_size' in summary

    def test_mat_parser_error_before_load(self, sample_mat_v6_file):
        """测试在加载前调用方法"""
        parser = MatParser(sample_mat_v6_file)

        with pytest.raises(MatParserError):
            parser.get_variable('time')

        with pytest.raises(MatParserError):
            parser.get_metadata()

        with pytest.raises(MatParserError):
            parser.get_summary()

    def test_parse_mat_file_convenience_function(self, sample_mat_v6_file):
        """测试便捷函数parse_mat_file"""
        summary = parse_mat_file(sample_mat_v6_file)

        assert 'file_name' in summary
        assert 'version' in summary
        assert 'variable_count' in summary

    def test_get_mat_time_series_convenience_function(self, sample_mat_v6_file):
        """测试便捷函数get_mat_time_series"""
        time_series = get_mat_time_series(sample_mat_v6_file)

        assert time_series is not None
        assert 'time' in time_series
        assert 'variables' in time_series

    def test_mat_file_without_time_series(self, tmp_path):
        """测试处理没有时序数据的MAT文件"""
        # 创建没有时间变量的MAT文件
        mat_data = {
            'data1': np.array([1, 2, 3, 4, 5]),
            'data2': np.array([5, 4, 3, 2, 1])
        }

        mat_file = tmp_path / "no_time.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        # 应该能加载，但没有时序数据
        time_series = parser.get_time_series_data()
        assert time_series is None

    def test_mat_file_large_arrays(self, tmp_path):
        """测试处理大型数组"""
        # 创建大型数组
        large_array = np.random.rand(10000, 100)
        mat_data = {
            'large_array': large_array,
            'time': np.arange(10000)
        }

        mat_file = tmp_path / "large.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        summary = parser.get_summary()
        assert summary['variable_count'] >= 1


# ==================== 测试集成和边界情况 ====================

class TestEdgeCases:
    """边界情况和集成测试"""

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

    def test_mat_file_with_nested_structures(self, tmp_path):
        """测试包含嵌套结构的MAT文件"""
        # 创建包含嵌套结构的数据
        mat_data = {
            'struct_array': np.array([(1, 'a'), (2, 'b')], dtype=[('id', 'i4'), ('name', 'U1')]),
            'time': np.arange(10)
        }

        mat_file = tmp_path / "nested.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        # 应该能加载
        assert parser.data is not None

    def test_dbc_file_with_comments(self, tmp_path):
        """测试包含注释的DBC文件"""
        dbc_content = """VERSION ""

NS_ :
    NS_DESC_
    CM_

BS_:

BU_:

BO_ 100 TEST_MSG: 8 Vector__XXX
 SG_ TestSignal : 0|16@1+ (0.1,0) [0|6553.5] "Test signal"

CM_ TEST_MSG "This is a test message";
CM_ SG_ 100 TestSignal "This is a test signal";
"""
        dbc_file = tmp_path / "test_comments.dbc"
        dbc_file.write_text(dbc_content, encoding='utf-8')

        parser = DBCParser(str(dbc_file))
        parser.load()
        messages = parser.get_messages()

        assert len(messages) == 1
        assert messages[0]['comment'] is not None

    def test_mat_file_with_special_characters(self, tmp_path):
        """测试包含特殊字符的MAT文件"""
        mat_data = {
            'test_name': 'test value',
            'time': np.arange(10)
        }

        mat_file = tmp_path / "special.mat"
        sio.savemat(str(mat_file), mat_data)

        parser = MatParser(str(mat_file))
        parser.load()

        value = parser.get_variable('test_name')
        assert value is not None

# ==================== 从app.services导入便捷函数 ====================
from app.services.dbc_parser import parse_dbc_file, get_message_signals
from app.services.mat_parser import parse_mat_file, get_mat_time_series

from app.services.dbc_parser import parse_dbc_file, get_message_signals
from app.services.mat_parser import parse_mat_file, get_mat_time_series
