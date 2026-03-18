"""
文件解析服务

提供多种文件格式的解析功能：
- CSV文件（使用pandas）
- Excel文件（使用openpyxl）
- DBC文件（使用cantools）
- MATLAB .mat文件（使用scipy，支持v6和v7.3）
- Vector CAN log文件（使用python-can）
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from scipy import io as sio
import can
import cantools
import h5py

# 配置日志
logger = logging.getLogger(__name__)


class FileParserError(Exception):
    """文件解析错误"""
    pass


class FileParser:
    """文件解析器基类"""

    def __init__(self):
        self.parser_map = {
            'csv': self.parse_csv,
            'excel': self.parse_excel,
            'mat': self.parse_mat,
            'dbc': self.parse_dbc,
            'log': self.parse_can_log
        }

    def parse(self, file_path: str, file_type: str, **kwargs) -> Dict[str, Any]:
        """
        根据文件类型解析文件

        Args:
            file_path: 文件路径
            file_type: 文件类型（csv, excel, mat, dbc, log）
            **kwargs: 额外的解析参数

        Returns:
            包含解析结果的字典

        Raises:
            FileParserError: 当文件解析失败时
        """
        try:
            file_type = file_type.lower()

            if file_type not in self.parser_map:
                raise FileParserError(f"Unsupported file type: {file_type}")

            parser = self.parser_map[file_type]
            result = parser(file_path, **kwargs)

            logger.info(f"Successfully parsed {file_type} file: {file_path}")
            return result

        except FileParserError:
            raise
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}", exc_info=True)
            raise FileParserError(f"Failed to parse file: {str(e)}")

    def parse_csv(
        self,
        file_path: str,
        encoding: str = 'utf-8',
        delimiter: str = ',',
        header: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        解析CSV文件

        Args:
            file_path: 文件路径
            encoding: 文件编码
            delimiter: 分隔符
            header: 表头行号
            **kwargs: 传递给pandas.read_csv的额外参数

        Returns:
            包含解析结果的字典
        """
        try:
            # 使用pandas读取CSV
            df = pd.read_csv(
                file_path,
                encoding=encoding,
                delimiter=delimiter,
                header=header,
                **kwargs
            )

            # 数据验证
            if df.empty:
                raise FileParserError("CSV file is empty")

            # 转换为字典格式
            data = df.to_dict('records')

            return {
                'file_type': 'csv',
                'columns': list(df.columns),
                'row_count': len(df),
                'data': data,
                'sample_data': df.head(10).to_dict('records'),
                'data_types': df.dtypes.astype(str).to_dict()
            }

        except pd.errors.EmptyDataError:
            raise FileParserError("CSV file is empty")
        except pd.errors.ParserError as e:
            raise FileParserError(f"CSV parsing error: {str(e)}")
        except Exception as e:
            raise FileParserError(f"Error reading CSV file: {str(e)}")

    def parse_excel(
        self,
        file_path: str,
        sheet_name: Optional[str] = None,
        header: int = 0,
        **kwargs
    ) -> Dict[str, Any]:
        """
        解析Excel文件

        Args:
            file_path: 文件路径
            sheet_name: 工作表名称（None表示读取第一个工作表）
            header: 表头行号
            **kwargs: 传递给pandas.read_excel的额外参数

        Returns:
            包含解析结果的字典
        """
        try:
            # 使用pandas读取Excel
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=header,
                engine='openpyxl',
                **kwargs
            )

            # 数据验证
            if df.empty:
                raise FileParserError("Excel file is empty")

            # 转换为字典格式
            data = df.to_dict('records')

            return {
                'file_type': 'excel',
                'sheet_name': sheet_name or 'Sheet1',
                'columns': list(df.columns),
                'row_count': len(df),
                'data': data,
                'sample_data': df.head(10).to_dict('records'),
                'data_types': df.dtypes.astype(str).to_dict()
            }

        except Exception as e:
            raise FileParserError(f"Error reading Excel file: {str(e)}")

    def parse_mat(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        解析MATLAB .mat文件（支持v6和v7.3格式）

        Args:
            file_path: 文件路径
            **kwargs: 额外的解析参数

        Returns:
            包含解析结果的字典
        """
        try:
            mat_data = {}

            # 尝试使用scipy.io.loadmat（支持v6和v7格式）
            try:
                mat_data = sio.loadmat(file_path, struct_as_record=False, squeeze_me=True)
                mat_version = 'v6/v7'
            except NotImplementedError:
                # 如果是v7.3格式，使用h5py
                try:
                    with h5py.File(file_path, 'r') as f:
                        for key in f.keys():
                            # 只读取数值数据
                            if isinstance(f[key], h5py.Dataset):
                                try:
                                    mat_data[key] = f[key][:]
                                except Exception:
                                    mat_data[key] = str(f[key])
                    mat_version = 'v7.3'
                except Exception as e:
                    raise FileParserError(f"Failed to parse MAT v7.3 file: {str(e)}")

            # 过滤掉MATLAB的内部变量
            internal_vars = {'__header__', '__version__', '__globals__'}
            filtered_data = {k: v for k, v in mat_data.items() if k not in internal_vars}

            if not filtered_data:
                raise FileParserError("No data found in MAT file")

            # 转换数据为可序列化格式
            serializable_data = {}
            for key, value in filtered_data.items():
                serializable_data[key] = self._serialize_matlab_value(value)

            return {
                'file_type': 'mat',
                'mat_version': mat_version,
                'variables': list(filtered_data.keys()),
                'data': serializable_data,
                'variable_info': self._get_variable_info(filtered_data)
            }

        except FileParserError:
            raise
        except Exception as e:
            raise FileParserError(f"Error reading MAT file: {str(e)}")

    def _serialize_matlab_value(self, value: Any) -> Any:
        """
        将MATLAB值序列化为Python可序列化格式

        Args:
            value: MATLAB值

        Returns:
            可序列化的Python值
        """
        import numpy as np

        if isinstance(value, np.ndarray):
            if value.ndim == 0:
                return value.item()
            elif value.ndim == 1:
                return value.tolist()
            else:
                return value.tolist()
        elif isinstance(value, (np.integer, np.int64, np.int32)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32)):
            return float(value)
        elif isinstance(value, np.bool_):
            return bool(value)
        elif isinstance(value, str):
            return value
        else:
            return str(value)

    def _get_variable_info(self, data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        获取MATLAB变量的信息

        Args:
            data: MATLAB数据字典

        Returns:
            变量信息字典
        """
        info = {}
        for key, value in data.items():
            info[key] = {
                'type': type(value).__name__,
                'shape': getattr(value, 'shape', None),
                'size': getattr(value, 'size', None)
            }
        return info

    def parse_dbc(self, file_path: str, **kwargs) -> Dict[str, Any]:
        """
        解析DBC文件

        Args:
            file_path: 文件路径
            **kwargs: 额外的解析参数

        Returns:
            包含解析结果的字典
        """
        try:
            # 使用cantools解析DBC文件
            db = cantools.database.load_file(file_path)

            # 提取消息和信号信息
            messages_info = []
            for message in db.messages:
                signals_info = []
                for signal in message.signals:
                    signals_info.append({
                        'name': signal.name,
                        'start': signal.start,
                        'length': signal.length,
                        'byte_order': signal.byte_order,
                        'is_signed': signal.is_signed,
                        'scale': signal.scale,
                        'offset': signal.offset,
                        'minimum': signal.minimum,
                        'maximum': signal.maximum,
                        'unit': signal.unit,
                        'comment': signal.comment,
                        'enumeration': signal.enumeration
                    })

                messages_info.append({
                    'frame_id': message.frame_id,
                    'name': message.name,
                    'length': message.length,
                    'comment': message.comment,
                    'signals': signals_info,
                    'is_extended_frame': message.is_extended_frame
                })

            return {
                'file_type': 'dbc',
                'version': db.version,
                'messages_count': len(db.messages),
                'nodes': [node.name for node in db.nodes],
                'messages': messages_info
            }

        except Exception as e:
            raise FileParserError(f"Error reading DBC file: {str(e)}")

    def parse_can_log(
        self,
        file_path: str,
        channel: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        解析Vector CAN log文件

        Args:
            file_path: 文件路径
            channel: 通道号（可选）
            **kwargs: 额外的解析参数

        Returns:
            包含解析结果的字典
        """
        try:
            # 根据文件扩展名选择日志类型
            ext = Path(file_path).suffix.lower()

            if ext == '.log':
                log_type = 'vector'
            elif ext == '.blf':
                log_type = 'blf'
            elif ext == '.asc':
                log_type = 'asc'
            else:
                log_type = 'vector'  # 默认

            messages = []

            # 使用python-can读取CAN日志
            for msg in can.LogReader(file_path):
                messages.append({
                    'timestamp': msg.timestamp,
                    'arbitration_id': msg.arbitration_id,
                    'is_extended_id': msg.is_extended_id,
                    'is_remote_frame': msg.is_remote_frame,
                    'is_error_frame': msg.is_error_frame,
                    'channel': msg.channel,
                    'dlc': msg.dlc,
                    'data': list(msg.data),
                    'data_hex': msg.data.hex()
                })

            if not messages:
                raise FileParserError("No messages found in CAN log file")

            # 统计信息
            arbitration_ids = set(msg['arbitration_id'] for msg in messages)

            return {
                'file_type': 'log',
                'log_type': log_type,
                'message_count': len(messages),
                'unique_ids': len(arbitration_ids),
                'time_range': {
                    'start': min(msg['timestamp'] for msg in messages),
                    'end': max(msg['timestamp'] for msg in messages)
                },
                'messages': messages[:100],  # 只返回前100条消息作为示例
                'arbitration_ids': list(arbitration_ids)
            }

        except Exception as e:
            raise FileParserError(f"Error reading CAN log file: {str(e)}")


# 创建全局解析器实例
file_parser = FileParser()


def parse_file(file_path: str, file_type: str, **kwargs) -> Dict[str, Any]:
    """
    解析文件的便捷函数

    Args:
        file_path: 文件路径
        file_type: 文件类型
        **kwargs: 额外的解析参数

    Returns:
        包含解析结果的字典

    Raises:
        FileParserError: 当文件解析失败时
    """
    return file_parser.parse(file_path, file_type, **kwargs)
