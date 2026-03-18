"""
MATLAB .mat文件解析服务

支持MATLAB v6格式（使用scipy.io）和MATLAB v7.3格式（使用h5py）。
提取时序数据和元数据，用于车载控制器测试数据分析。
"""
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import h5py
from scipy import io as sio


# 配置日志
logger = logging.getLogger(__name__)


class MatParserError(Exception):
    """MAT文件解析错误基类"""
    pass


class FileFormatError(MatParserError):
    """文件格式错误"""
    pass


class MatVersionError(MatParserError):
    """MAT版本不支持错误"""
    pass


class MatParser:
    """
    MAT文件解析器

    支持MATLAB v4、v6、v7和v7.3格式的文件解析。
    自动检测文件版本并使用相应的解析方法。
    """

    def __init__(self, mat_file_path: str):
        """
        初始化MAT解析器

        Args:
            mat_file_path: MAT文件路径

        Raises:
            FileFormatError: 文件不存在或格式不支持时
        """
        self.mat_file_path = Path(mat_file_path)
        self.version: Optional[str] = None
        self.data: Optional[Dict[str, Any]] = None
        self.metadata: Optional[Dict[str, Any]] = None

        if not self.mat_file_path.exists():
            raise FileFormatError(f"MAT file not found: {self.mat_file_path}")

        if self.mat_file_path.suffix.lower() != '.mat':
            raise FileFormatError(
                f"Invalid file extension: {self.mat_file_path.suffix}. "
                f"Expected .mat"
            )

    def detect_version(self) -> str:
        """
        检测MAT文件版本

        Returns:
            文件版本字符串：'v4', 'v6', 'v7', 'v7.3'

        Raises:
            MatVersionError: 无法检测文件版本时
        """
        try:
            # 尝试打开为HDF5文件（v7.3格式）
            with h5py.File(self.mat_file_path, 'r') as f:
                self.version = 'v7.3'
                logger.info("Detected MAT file version: v7.3 (HDF5)")
                return self.version

        except Exception as hdf5_error:
            try:
                # 尝试用scipy.io.loadmat加载（v4, v6, v7格式）
                mat_data = sio.loadmat(self.mat_file_path)
                # 检查__header__字段判断版本
                header = mat_data.get('__header__', b'')
                header_str = header.decode('utf-8', errors='ignore') if isinstance(header, bytes) else str(header)

                if 'MATLAB 5.0' in header_str:
                    self.version = 'v6'
                elif 'MATLAB 7.0' in header_str or 'MATLAB 7.3' not in header_str:
                    self.version = 'v7'
                else:
                    self.version = 'v4'

                logger.info(f"Detected MAT file version: {self.version}")
                return self.version

            except Exception as scipy_error:
                raise MatVersionError(
                    f"Failed to detect MAT file version: "
                    f"HDF5 error: {str(hdf5_error)}, "
                    f"SciPy error: {str(scipy_error)}"
                )

    def load(self) -> None:
        """
        加载MAT文件

        Raises:
            MatParserError: 文件加载失败时
        """
        if not self.version:
            self.detect_version()

        try:
            if self.version == 'v7.3':
                self._load_v73()
            else:
                self._load_scipy()

            # 提取元数据
            self._extract_metadata()

            logger.info(
                f"Successfully loaded MAT file: {self.mat_file_path.name}, "
                f"version: {self.version}, "
                f"variables: {len(self.data)}"
            )

        except Exception as e:
            logger.error(f"Failed to load MAT file: {str(e)}", exc_info=True)
            raise MatParserError(f"Failed to load MAT file: {str(e)}")

    def _load_v73(self) -> None:
        """加载MATLAB v7.3格式文件（使用h5py）"""
        self.data = {}

        def _traverse_hdf5(name, obj):
            """递归遍历HDF5文件"""
            if isinstance(obj, h5py.Dataset):
                try:
                    data = obj[()]
                    # 转换numpy数组为Python列表（如果需要）
                    if isinstance(data, np.ndarray):
                        if data.dtype.kind in ['U', 'S']:  # 字符串数组
                            data = data.astype(str).tolist()
                        elif data.size == 1:  # 标量
                            data = data.item()
                        else:  # 数组
                            data = data.tolist()
                    self.data[name] = data
                except Exception as e:
                    logger.warning(f"Failed to load dataset {name}: {str(e)}")

        with h5py.File(self.mat_file_path, 'r') as f:
            f.visititems(_traverse_hdf5)

    def _load_scipy(self) -> None:
        """加载MATLAB v4/v6/v7格式文件（使用scipy.io）"""
        mat_data = sio.loadmat(self.mat_file_path)
        self.data = {}

        # 过滤掉内部变量（以__开头和结尾）
        for key, value in mat_data.items():
            if not key.startswith('__'):
                # 转换numpy数组为Python列表
                if isinstance(value, np.ndarray):
                    if value.dtype.kind in ['U', 'S']:  # 字符串数组
                        value = value.astype(str).tolist()
                    elif value.size == 1:  # 标量
                        value = value.item()
                    else:  # 数组
                        value = value.tolist()
                self.data[key] = value

    def _extract_metadata(self) -> None:
        """提取文件元数据"""
        self.metadata = {
            'file_name': self.mat_file_path.name,
            'file_size': self.mat_file_path.stat().st_size,
            'version': self.version,
            'variable_names': list(self.data.keys()) if self.data else [],
            'variable_count': len(self.data) if self.data else 0
        }

        # 尝试提取时序数据信息
        time_series_info = self._extract_time_series_info()
        if time_series_info:
            self.metadata['time_series'] = time_series_info

    def _extract_time_series_info(self) -> Optional[Dict[str, Any]]:
        """
        尝试识别和提取时序数据信息

        Returns:
            时序数据信息字典，如果未找到时序数据则返回None
        """
        if not self.data:
            return None

        # 常见的时间变量名称
        time_keywords = ['time', 't', 'timestamp', 'Time', 'T', 'Timestamp']
        time_variable = None

        # 查找时间变量
        for var_name in self.data.keys():
            if var_name.lower().startswith(tuple(kw.lower() for kw in time_keywords)):
                time_variable = var_name
                break

        if not time_variable:
            return None

        # 检查时间变量是否为1D数组
        time_data = self.data[time_variable]
        if not isinstance(time_data, (list, np.ndarray)):
            return None

        time_array = np.array(time_data)
        if time_array.ndim != 1:
            return None

        # 提取时序信息
        time_series_info = {
            'time_variable': time_variable,
            'time_points': len(time_array),
            'time_start': float(time_array[0]) if len(time_array) > 0 else None,
            'time_end': float(time_array[-1]) if len(time_array) > 0 else None,
            'time_step': float(time_array[1] - time_array[0]) if len(time_array) > 1 else None
        }

        # 查找其他可能与时序相关的变量
        signal_variables = []
        for var_name in self.data.keys():
            if var_name != time_variable:
                var_data = self.data[var_name]
                if isinstance(var_data, (list, np.ndarray)):
                    var_array = np.array(var_data)
                    if var_array.ndim >= 1 and len(var_array) == len(time_array):
                        signal_variables.append(var_name)

        time_series_info['signal_variables'] = signal_variables
        time_series_info['signal_count'] = len(signal_variables)

        return time_series_info

    def get_variable(self, variable_name: str) -> Any:
        """
        获取指定变量的数据

        Args:
            variable_name: 变量名称

        Returns:
            变量数据

        Raises:
            MatParserError: 变量不存在时
        """
        if not self.data:
            raise MatParserError("MAT file not loaded. Call load() first.")

        if variable_name not in self.data:
            raise MatParserError(
                f"Variable '{variable_name}' not found. "
                f"Available variables: {list(self.data.keys())}"
            )

        return self.data[variable_name]

    def get_metadata(self) -> Dict[str, Any]:
        """
        获取文件元数据

        Returns:
            元数据字典

        Raises:
            MatParserError: 文件未加载时
        """
        if not self.metadata:
            raise MatParserError("MAT file not loaded. Call load() first.")

        return self.metadata

    def get_time_series_data(self) -> Optional[Dict[str, Any]]:
        """
        获取时序数据

        Returns:
            时序数据字典，包含时间向量和相关信号数据。
            如果未找到时序数据则返回None。

        Raises:
            MatParserError: 文件未加载时
        """
        if not self.data:
            raise MatParserError("MAT file not loaded. Call load() first.")

        time_info = self._extract_time_series_info()
        if not time_info:
            return None

        time_variable = time_info['time_variable']
        signal_variables = time_info.get('signal_variables', [])

        time_series = {
            'time': self.data[time_variable],
            'variables': {}
        }

        for var_name in signal_variables:
            time_series['variables'][var_name] = self.data[var_name]

        return time_series

    def get_variable_info(self, variable_name: str) -> Dict[str, Any]:
        """
        获取变量的详细信息

        Args:
            variable_name: 变量名称

        Returns:
            变量信息字典，包含类型、形状、大小等

        Raises:
            MatParserError: 变量不存在时
        """
        if not self.data:
            raise MatParserError("MAT file not loaded. Call load() first.")

        if variable_name not in self.data:
            raise MatParserError(
                f"Variable '{variable_name}' not found. "
                f"Available variables: {list(self.data.keys())}"
            )

        data = self.data[variable_name]

        info = {
            'name': variable_name,
            'type': type(data).__name__,
            'dtype': str(type(data))
        }

        if isinstance(data, (list, np.ndarray)):
            data_array = np.array(data)
            info.update({
                'dtype': str(data_array.dtype),
                'shape': data_array.shape,
                'size': data_array.size,
                'ndim': data_array.ndim
            })
        else:
            info['value'] = data

        return info

    def get_all_variables_info(self) -> List[Dict[str, Any]]:
        """
        获取所有变量的信息

        Returns:
            变量信息列表

        Raises:
            MatParserError: 文件未加载时
        """
        if not self.data:
            raise MatParserError("MAT file not loaded. Call load() first.")

        return [self.get_variable_info(var_name) for var_name in self.data.keys()]

    def extract_as_dataframe(self) -> Dict[str, Any]:
        """
        尝试将数据提取为DataFrame格式

        Returns:
            包含数据和列信息的字典

        Raises:
            MatParserError: 文件未加载或无法转换为DataFrame时
        """
        if not self.data:
            raise MatParserError("MAT file not loaded. Call load() first.")

        # 尝试找到时序数据
        time_series = self.get_time_series_data()
        if not time_series:
            raise MatParserError("No time series data found in MAT file")

        # 准备DataFrame数据
        data_dict = {'time': time_series['time']}
        data_dict.update(time_series['variables'])

        return {
            'data': data_dict,
            'columns': list(data_dict.keys()),
            'length': len(data_dict['time'])
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        获取MAT文件的摘要信息

        Returns:
            摘要信息字典

        Raises:
            MatParserError: 文件未加载时
        """
        if not self.metadata:
            raise MatParserError("MAT file not loaded. Call load() first.")

        summary = self.metadata.copy()

        # 添加变量类型分布
        type_counts = {}
        for var_name, var_data in self.data.items():
            var_type = type(var_data).__name__
            type_counts[var_type] = type_counts.get(var_type, 0) + 1

        summary['variable_types'] = type_counts

        # 添加变量大小信息
        total_size = 0
        for var_data in self.data.values():
            if isinstance(var_data, (list, np.ndarray)):
                total_size += np.array(var_data).nbytes
            elif isinstance(var_data, (int, float, bool)):
                total_size += 8  # 假设8字节
            elif isinstance(var_data, str):
                total_size += len(var_data.encode('utf-8'))

        summary['estimated_data_size'] = total_size

        return summary


def parse_mat_file(mat_file_path: str) -> Dict[str, Any]:
    """
    便捷函数：解析MAT文件并返回摘要信息

    Args:
        mat_file_path: MAT文件路径

    Returns:
        包含MAT文件摘要信息的字典

    Raises:
        FileFormatError: 文件格式不支持时
        MatParserError: 文件解析失败时
    """
    parser = MatParser(mat_file_path)
    parser.load()
    return parser.get_summary()


def get_mat_time_series(mat_file_path: str) -> Optional[Dict[str, Any]]:
    """
    便捷函数：从MAT文件获取时序数据

    Args:
        mat_file_path: MAT文件路径

    Returns:
        时序数据字典，如果未找到时序数据则返回None

    Raises:
        FileFormatError: 文件格式不支持时
        MatParserError: 文件解析失败时
    """
    parser = MatParser(mat_file_path)
    parser.load()
    return parser.get_time_series_data()
