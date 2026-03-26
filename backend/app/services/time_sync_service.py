"""
时间同步服务

提供多数据源时间对齐和重采样功能
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
from scipy import interpolate

logger = logging.getLogger(__name__)


class TimeSyncError(Exception):
    """时间同步错误"""

    pass


class TimeSyncService:
    """
    时间同步服务

    处理多数据源的时间对齐、重采样和插值
    """

    INTERPOLATION_METHODS = ["linear", "spline", "step", "nearest"]

    def __init__(self):
        self.time_column = "time"
        self.sync_metadata = {}

    def detect_time_column(self, data: Dict[str, np.ndarray]) -> Optional[str]:
        """
        自动检测时间列

        Args:
            data: 信号数据字典

        Returns:
            时间列名称
        """
        time_candidates = [
            "time",
            "Time",
            "t",
            "T",
            "timestamp",
            "Timestamp",
            "timestamp_ms",
            "time_s",
            "Time_s",
            "时间",
        ]

        for candidate in time_candidates:
            if candidate in data:
                return candidate

        for name, values in data.items():
            if isinstance(values, np.ndarray) and len(values) > 1:
                if np.all(np.diff(values) >= 0):
                    if np.std(np.diff(values)) < np.mean(np.diff(values)) * 0.5:
                        return name

        return None

    def get_time_info(self, data: Dict[str, np.ndarray], time_col: str = None) -> Dict[str, Any]:
        """
        获取时间信息

        Args:
            data: 信号数据字典
            time_col: 时间列名称

        Returns:
            时间信息字典
        """
        if time_col is None:
            time_col = self.detect_time_column(data)

        if time_col is None or time_col not in data:
            return {
                "time_column": None,
                "duration": 0,
                "sample_count": 0,
                "sampling_rate": 0,
                "is_uniform": False,
            }

        time_data = data[time_col]

        if len(time_data) < 2:
            return {
                "time_column": time_col,
                "duration": 0,
                "sample_count": len(time_data),
                "sampling_rate": 0,
                "is_uniform": False,
            }

        duration = float(time_data[-1] - time_data[0])
        sample_count = len(time_data)

        dt = np.diff(time_data)
        mean_dt = np.mean(dt)
        std_dt = np.std(dt)

        is_uniform = std_dt < mean_dt * 0.1 if mean_dt > 0 else False
        sampling_rate = 1.0 / mean_dt if mean_dt > 0 else 0

        return {
            "time_column": time_col,
            "start_time": float(time_data[0]),
            "end_time": float(time_data[-1]),
            "duration": duration,
            "sample_count": sample_count,
            "mean_dt": float(mean_dt),
            "std_dt": float(std_dt),
            "sampling_rate": float(sampling_rate),
            "is_uniform": is_uniform,
        }

    def align_time_sources(
        self,
        data_sources: List[Dict[str, np.ndarray]],
        time_columns: List[str] = None,
        sync_events: List[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, np.ndarray]], Dict[str, Any]]:
        """
        对齐多个数据源的时间

        Args:
            data_sources: 多个数据源列表
            time_columns: 各数据源的时间列名称
            sync_events: 同步事件配置

        Returns:
            对齐后的数据源列表和同步元数据
        """
        if not data_sources:
            raise TimeSyncError("No data sources provided")

        if time_columns is None:
            time_columns = [self.detect_time_column(ds) for ds in data_sources]

        time_infos = []
        for i, (ds, tc) in enumerate(zip(data_sources, time_columns)):
            info = self.get_time_info(ds, tc)
            info["source_index"] = i
            time_infos.append(info)

        time_offsets = [0.0] * len(data_sources)

        if sync_events:
            time_offsets = self._calculate_time_offsets(data_sources, time_columns, sync_events)

        common_start = max(
            info["start_time"] - offset
            for info, offset in zip(time_infos, time_offsets)
            if info["time_column"] is not None
        )

        common_end = min(
            info["end_time"] - offset
            for info, offset in zip(time_infos, time_offsets)
            if info["time_column"] is not None
        )

        max_sampling_rate = max(
            info["sampling_rate"] for info in time_infos if info["sampling_rate"] > 0
        )

        aligned_sources = []
        for i, (ds, tc, offset) in enumerate(zip(data_sources, time_columns, time_offsets)):
            if tc is None:
                aligned_sources.append(ds)
                continue

            time_data = ds[tc] - offset

            mask = (time_data >= common_start) & (time_data <= common_end)

            aligned_ds = {}
            for key, values in ds.items():
                if key == tc:
                    aligned_ds[key] = time_data[mask]
                else:
                    aligned_ds[key] = values[mask] if len(values) == len(ds[tc]) else values

            aligned_sources.append(aligned_ds)

        sync_metadata = {
            "time_offsets": time_offsets,
            "common_start": float(common_start),
            "common_end": float(common_end),
            "common_duration": float(common_end - common_start),
            "target_sampling_rate": float(max_sampling_rate),
            "time_infos": time_infos,
            "sync_events_used": len(sync_events) if sync_events else 0,
        }

        self.sync_metadata = sync_metadata

        return aligned_sources, sync_metadata

    def _calculate_time_offsets(
        self,
        data_sources: List[Dict[str, np.ndarray]],
        time_columns: List[str],
        sync_events: List[Dict[str, Any]],
    ) -> List[float]:
        """
        计算时间偏移量

        Args:
            data_sources: 数据源列表
            time_columns: 时间列名称列表
            sync_events: 同步事件配置

        Returns:
            时间偏移量列表
        """
        offsets = [0.0] * len(data_sources)

        for event in sync_events:
            event_name = event.get("event_name")
            signal_name = event.get("signal_name")
            condition = event.get("condition")

            event_times = []
            for i, (ds, tc) in enumerate(zip(data_sources, time_columns)):
                if tc is None or signal_name not in ds:
                    event_times.append(None)
                    continue

                try:
                    if condition:
                        condition_str = condition.replace(signal_name, f"ds['{signal_name}']")
                        mask = eval(condition_str)
                    else:
                        mask = ds[signal_name] > 0

                    indices = np.where(mask)[0]
                    if len(indices) > 0:
                        event_time = ds[tc][indices[0]]
                        event_times.append(float(event_time))
                    else:
                        event_times.append(None)
                except:
                    event_times.append(None)

            valid_times = [t for t in event_times if t is not None]
            if valid_times:
                reference_time = min(valid_times)
                for i, t in enumerate(event_times):
                    if t is not None:
                        offsets[i] = t - reference_time

        return offsets

    def resample_signal(
        self,
        time_data: np.ndarray,
        signal_data: np.ndarray,
        target_time: np.ndarray,
        method: str = "linear",
    ) -> np.ndarray:
        """
        重采样信号

        Args:
            time_data: 原始时间数据
            signal_data: 原始信号数据
            target_time: 目标时间数据
            method: 插值方法

        Returns:
            重采样后的信号数据
        """
        if len(time_data) < 2 or len(signal_data) < 2:
            return np.zeros(len(target_time))

        valid_mask = ~(np.isnan(time_data) | np.isnan(signal_data))
        time_valid = time_data[valid_mask]
        signal_valid = signal_data[valid_mask]

        if len(time_valid) < 2:
            return np.full(len(target_time), np.nan)

        sort_idx = np.argsort(time_valid)
        time_sorted = time_valid[sort_idx]
        signal_sorted = signal_valid[sort_idx]

        unique_mask = np.concatenate([[True], np.diff(time_sorted) > 1e-10])
        time_unique = time_sorted[unique_mask]
        signal_unique = signal_sorted[unique_mask]

        if len(time_unique) < 2:
            return np.full(len(target_time), np.nan)

        try:
            if method == "linear":
                interp_func = interpolate.interp1d(
                    time_unique,
                    signal_unique,
                    kind="linear",
                    bounds_error=False,
                    fill_value="extrapolate",
                )
            elif method == "spline":
                if len(time_unique) >= 4:
                    interp_func = interpolate.interp1d(
                        time_unique,
                        signal_unique,
                        kind="cubic",
                        bounds_error=False,
                        fill_value="extrapolate",
                    )
                else:
                    interp_func = interpolate.interp1d(
                        time_unique,
                        signal_unique,
                        kind="linear",
                        bounds_error=False,
                        fill_value="extrapolate",
                    )
            elif method == "step":
                interp_func = interpolate.interp1d(
                    time_unique,
                    signal_unique,
                    kind="previous",
                    bounds_error=False,
                    fill_value=(signal_unique[0], signal_unique[-1]),
                )
            elif method == "nearest":
                interp_func = interpolate.interp1d(
                    time_unique,
                    signal_unique,
                    kind="nearest",
                    bounds_error=False,
                    fill_value="extrapolate",
                )
            else:
                interp_func = interpolate.interp1d(
                    time_unique,
                    signal_unique,
                    kind="linear",
                    bounds_error=False,
                    fill_value="extrapolate",
                )

            result = interp_func(target_time)
            return result

        except Exception as e:
            logger.warning(f"Interpolation failed: {str(e)}")
            return np.full(len(target_time), np.nan)

    def resample_data(
        self,
        data: Dict[str, np.ndarray],
        target_sampling_rate: float = None,
        target_time: np.ndarray = None,
        interpolation_method: str = "linear",
        time_column: str = None,
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        重采样整个数据集

        Args:
            data: 原始数据字典
            target_sampling_rate: 目标采样率
            target_time: 目标时间数组
            interpolation_method: 插值方法
            time_column: 时间列名称

        Returns:
            重采样后的数据和元数据
        """
        if time_column is None:
            time_column = self.detect_time_column(data)

        if time_column is None or time_column not in data:
            raise TimeSyncError("No time column found in data")

        time_data = data[time_column]

        if target_time is None:
            if target_sampling_rate is None:
                time_info = self.get_time_info(data, time_column)
                target_sampling_rate = time_info["sampling_rate"]

            start_time = time_data[0]
            end_time = time_data[-1]
            duration = end_time - start_time

            num_samples = int(duration * target_sampling_rate) + 1
            target_time = np.linspace(start_time, end_time, num_samples)

        resampled_data = {time_column: target_time}

        interpolation_stats = {}

        for signal_name, signal_data in data.items():
            if signal_name == time_column:
                continue

            if len(signal_data) != len(time_data):
                resampled_data[signal_name] = signal_data
                continue

            resampled_signal = self.resample_signal(
                time_data, signal_data, target_time, interpolation_method
            )

            resampled_data[signal_name] = resampled_signal

            valid_count = np.sum(~np.isnan(resampled_signal))
            interpolation_stats[signal_name] = {
                "valid_count": int(valid_count),
                "nan_count": int(len(target_time) - valid_count),
                "valid_rate": float(valid_count / len(target_time)),
            }

        metadata = {
            "original_sample_count": len(time_data),
            "resampled_sample_count": len(target_time),
            "target_sampling_rate": float(target_sampling_rate) if target_sampling_rate else None,
            "interpolation_method": interpolation_method,
            "time_range": {"start": float(target_time[0]), "end": float(target_time[-1])},
            "interpolation_stats": interpolation_stats,
        }

        return resampled_data, metadata

    def merge_data_sources(
        self,
        data_sources: List[Dict[str, np.ndarray]],
        time_columns: List[str] = None,
        target_sampling_rate: float = None,
        interpolation_method: str = "linear",
    ) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
        """
        合并多个数据源

        Args:
            data_sources: 数据源列表
            time_columns: 时间列名称列表
            target_sampling_rate: 目标采样率
            interpolation_method: 插值方法

        Returns:
            合并后的数据和元数据
        """
        if not data_sources:
            raise TimeSyncError("No data sources to merge")

        if time_columns is None:
            time_columns = [self.detect_time_column(ds) for ds in data_sources]

        aligned_sources, align_metadata = self.align_time_sources(data_sources, time_columns)

        if target_sampling_rate is None:
            target_sampling_rate = align_metadata.get("target_sampling_rate", 100)

        common_start = align_metadata["common_start"]
        common_end = align_metadata["common_end"]
        duration = common_end - common_start

        num_samples = int(duration * target_sampling_rate) + 1
        target_time = np.linspace(common_start, common_end, num_samples)

        merged_data = {"time": target_time}
        merge_stats = {}

        for i, (ds, tc) in enumerate(zip(aligned_sources, time_columns)):
            if tc is None:
                continue

            time_data = ds[tc]

            for signal_name, signal_data in ds.items():
                if signal_name == tc:
                    continue

                unique_name = signal_name
                counter = 1
                while unique_name in merged_data:
                    unique_name = f"{signal_name}_{counter}"
                    counter += 1

                resampled = self.resample_signal(
                    time_data, signal_data, target_time, interpolation_method
                )

                merged_data[unique_name] = resampled

                merge_stats[unique_name] = {
                    "source_index": i,
                    "original_name": signal_name,
                    "valid_count": int(np.sum(~np.isnan(resampled))),
                }

        metadata = {
            "source_count": len(data_sources),
            "merged_signal_count": len(merged_data) - 1,
            "target_sampling_rate": float(target_sampling_rate),
            "interpolation_method": interpolation_method,
            "time_range": {
                "start": float(common_start),
                "end": float(common_end),
                "duration": float(duration),
            },
            "sample_count": len(target_time),
            "align_metadata": align_metadata,
            "merge_stats": merge_stats,
        }

        return merged_data, metadata

    def evaluate_sync_quality(
        self,
        original_data: Dict[str, np.ndarray],
        resampled_data: Dict[str, np.ndarray],
        time_column: str = None,
    ) -> Dict[str, Any]:
        """
        评估同步质量

        Args:
            original_data: 原始数据
            resampled_data: 重采样数据
            time_column: 时间列名称

        Returns:
            质量评估结果
        """
        if time_column is None:
            time_column = self.detect_time_column(original_data)

        quality_metrics = {}

        for signal_name in original_data:
            if signal_name == time_column:
                continue

            if signal_name not in resampled_data:
                continue

            original = original_data[signal_name]
            resampled = resampled_data[signal_name]

            valid_mask = ~np.isnan(resampled)
            valid_resampled = resampled[valid_mask]

            if len(valid_resampled) == 0:
                quality_metrics[signal_name] = {
                    "quality_score": 0,
                    "nan_ratio": 1.0,
                    "status": "poor",
                }
                continue

            nan_ratio = 1.0 - len(valid_resampled) / len(resampled)

            original_valid = original[~np.isnan(original)]
            resampled_valid = resampled[~np.isnan(resampled)]

            if len(original_valid) > 0 and len(resampled_valid) > 0:
                original_range = np.max(original_valid) - np.min(original_valid)
                resampled_range = np.max(resampled_valid) - np.min(resampled_valid)

                range_preservation = (
                    min(original_range, resampled_range) / max(original_range, resampled_range)
                    if max(original_range, resampled_range) > 0
                    else 1.0
                )

                original_mean = np.mean(original_valid)
                resampled_mean = np.mean(resampled_valid)
                mean_preservation = 1.0 - abs(original_mean - resampled_mean) / (
                    abs(original_mean) + 1e-10
                )
            else:
                range_preservation = 0
                mean_preservation = 0

            quality_score = (
                (1.0 - nan_ratio) * 0.4 + range_preservation * 0.3 + mean_preservation * 0.3
            )

            if quality_score >= 0.9:
                status = "excellent"
            elif quality_score >= 0.7:
                status = "good"
            elif quality_score >= 0.5:
                status = "acceptable"
            else:
                status = "poor"

            quality_metrics[signal_name] = {
                "quality_score": round(quality_score, 3),
                "nan_ratio": round(nan_ratio, 3),
                "range_preservation": round(range_preservation, 3),
                "mean_preservation": round(mean_preservation, 3),
                "status": status,
            }

        overall_score = np.mean([m["quality_score"] for m in quality_metrics.values()])

        return {
            "overall_quality_score": round(overall_score, 3),
            "signal_count": len(quality_metrics),
            "quality_metrics": quality_metrics,
            "recommendation": self._get_quality_recommendation(overall_score),
        }

    def _get_quality_recommendation(self, quality_score: float) -> str:
        """获取质量建议"""
        if quality_score >= 0.9:
            return "数据同步质量优秀，可直接用于分析"
        elif quality_score >= 0.7:
            return "数据同步质量良好，建议检查个别信号"
        elif quality_score >= 0.5:
            return "数据同步质量一般，建议调整插值方法或采样率"
        else:
            return "数据同步质量较差，建议检查时间对齐或数据源"


time_sync_service = TimeSyncService()
