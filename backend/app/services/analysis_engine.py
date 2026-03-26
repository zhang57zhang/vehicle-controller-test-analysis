"""
数据分析引擎

提供核心数据分析功能：
- 信号提取和映射执行
- 基础指标计算（范围检查、统计）
- 异常检测
- 自定义信号计算
"""

import logging
import re
import math
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

from app.services.file_parser import file_parser
from app.services.dbc_parser import DBCParser

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    """分析错误基类"""

    pass


class SignalExtractionError(AnalysisError):
    """信号提取错误"""

    pass


class IndicatorCalculationError(AnalysisError):
    """指标计算错误"""

    pass


class AnalysisEngine:
    """
    数据分析引擎

    负责执行数据分析的核心逻辑
    """

    def __init__(self):
        self.data: Optional[pd.DataFrame] = None
        self.signals: Dict[str, np.ndarray] = {}
        self.time_column: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def load_data(self, file_path: str, file_type: str) -> Dict[str, Any]:
        """
        加载测试数据文件

        Args:
            file_path: 文件路径
            file_type: 文件类型

        Returns:
            加载结果信息
        """
        try:
            result = file_parser.parse(file_path, file_type)

            if file_type == "csv":
                self._load_from_csv_result(result)
            elif file_type == "excel":
                self._load_from_excel_result(result)
            elif file_type == "mat":
                self._load_from_mat_result(result)
            elif file_type == "log":
                self._load_from_can_log_result(result)
            else:
                raise AnalysisError(f"Unsupported file type: {file_type}")

            self.metadata = {
                "file_path": file_path,
                "file_type": file_type,
                "loaded_at": datetime.now().isoformat(),
                "row_count": result.get("row_count", 0),
                "columns": result.get("columns", []),
            }

            logger.info(f"Loaded data from {file_path}: {len(self.signals)} signals")
            return {
                "status": "success",
                "signals": list(self.signals.keys()),
                "row_count": len(self.data) if self.data is not None else 0,
            }

        except Exception as e:
            logger.error(f"Error loading data: {str(e)}", exc_info=True)
            raise AnalysisError(f"Failed to load data: {str(e)}")

    def _load_from_csv_result(self, result: Dict[str, Any]):
        """从CSV解析结果加载数据"""
        data = result.get("data", [])
        if not data:
            raise AnalysisError("No data in CSV file")

        self.data = pd.DataFrame(data)
        self._extract_signals_from_dataframe()

    def _load_from_excel_result(self, result: Dict[str, Any]):
        """从Excel解析结果加载数据"""
        data = result.get("data", [])
        if not data:
            raise AnalysisError("No data in Excel file")

        self.data = pd.DataFrame(data)
        self._extract_signals_from_dataframe()

    def _load_from_mat_result(self, result: Dict[str, Any]):
        """从MAT解析结果加载数据"""
        data = result.get("data", {})
        if not data:
            raise AnalysisError("No data in MAT file")

        self.signals = {}
        time_candidates = ["time", "Time", "t", "T", "timestamp", "Timestamp"]

        for key, value in data.items():
            if isinstance(value, (list, np.ndarray)):
                arr = np.array(value)
                if arr.ndim == 1:
                    self.signals[key] = arr
                    if key in time_candidates and self.time_column is None:
                        self.time_column = key

        if self.signals:
            max_len = max(len(v) for v in self.signals.values())
            data_dict = {k: v for k, v in self.signals.items()}
            self.data = pd.DataFrame(data_dict)

    def _load_from_can_log_result(self, result: Dict[str, Any]):
        """从CAN日志解析结果加载数据"""
        messages = result.get("messages", [])
        if not messages:
            raise AnalysisError("No messages in CAN log file")

        df_data = []
        for msg in messages:
            df_data.append(
                {
                    "timestamp": msg.get("timestamp", 0),
                    "arbitration_id": msg.get("arbitration_id", 0),
                    "channel": msg.get("channel", 0),
                    "dlc": msg.get("dlc", 0),
                    "data_hex": msg.get("data_hex", ""),
                }
            )

        self.data = pd.DataFrame(df_data)
        self._extract_signals_from_dataframe()

    def _extract_signals_from_dataframe(self):
        """从DataFrame提取信号"""
        self.signals = {}
        time_candidates = ["time", "Time", "t", "T", "timestamp", "Timestamp", "timestamp_ms"]

        for col in self.data.columns:
            if col in time_candidates and self.time_column is None:
                self.time_column = col
            self.signals[col] = self.data[col].values

    def apply_signal_mappings(self, signal_mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        应用信号映射

        Args:
            signal_mappings: 信号映射配置列表

        Returns:
            映射结果信息
        """
        if not self.signals:
            raise SignalExtractionError("No signals loaded")

        mapped_signals = {}
        mapping_log = []

        for mapping in signal_mappings:
            alias = mapping.get("signal_alias")
            dbc_signal = mapping.get("dbc_signal")
            data_source = mapping.get("data_source_signal")
            unit_conversion = mapping.get("unit_conversion")

            source_signal = data_source or dbc_signal

            if source_signal and source_signal in self.signals:
                signal_data = self.signals[source_signal].copy()

                if unit_conversion:
                    formula = unit_conversion.get("formula", "x")
                    try:
                        signal_data = self._apply_conversion_formula(signal_data, formula)
                        mapping_log.append(
                            {
                                "alias": alias,
                                "source": source_signal,
                                "conversion": formula,
                                "status": "success",
                            }
                        )
                    except Exception as e:
                        mapping_log.append(
                            {
                                "alias": alias,
                                "source": source_signal,
                                "conversion": formula,
                                "status": "error",
                                "error": str(e),
                            }
                        )
                        continue

                mapped_signals[alias] = signal_data
                self.signals[alias] = signal_data
            else:
                mapping_log.append({"alias": alias, "source": source_signal, "status": "not_found"})

        logger.info(f"Applied {len(mapped_signals)} signal mappings")
        return {"mapped_count": len(mapped_signals), "mappings": mapping_log}

    def _apply_conversion_formula(self, data: np.ndarray, formula: str) -> np.ndarray:
        """
        应用单位转换公式

        Args:
            data: 原始数据
            formula: 转换公式（使用x作为变量）

        Returns:
            转换后的数据
        """
        safe_formula = formula.replace("x", "data")
        safe_formula = re.sub(r"[^0-9+\-*/().\sdata]", "", safe_formula)

        try:
            result = eval(safe_formula, {"data": data, "np": np, "math": math})
            return np.array(result, dtype=float)
        except Exception as e:
            raise AnalysisError(f"Formula evaluation error: {str(e)}")

    def calculate_custom_signals(self, custom_signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算自定义信号

        Args:
            custom_signals: 自定义信号配置列表

        Returns:
            计算结果信息
        """
        if not self.signals:
            raise SignalExtractionError("No signals loaded")

        calculated = []

        for custom in custom_signals:
            alias = custom.get("signal_alias")
            calculation = custom.get("calculation", "")
            input_signals = custom.get("input_signals", [])

            try:
                local_vars = {}
                for sig in input_signals:
                    if sig in self.signals:
                        local_vars[sig] = self.signals[sig]
                    else:
                        raise AnalysisError(f"Input signal '{sig}' not found")

                local_vars["np"] = np
                local_vars["math"] = math

                result = eval(calculation, {"__builtins__": {}}, local_vars)
                self.signals[alias] = np.array(result, dtype=float)

                calculated.append({"alias": alias, "status": "success"})

            except Exception as e:
                calculated.append({"alias": alias, "status": "error", "error": str(e)})

        return {
            "calculated_count": len([c for c in calculated if c["status"] == "success"]),
            "results": calculated,
        }

    def calculate_range_indicator(
        self,
        signal_name: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        unit: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        计算范围检查指标

        Args:
            signal_name: 信号名称
            min_value: 最小值
            max_value: 最大值
            unit: 单位

        Returns:
            指标结果
        """
        if signal_name not in self.signals:
            raise IndicatorCalculationError(f"Signal '{signal_name}' not found")

        signal_data = self.signals[signal_name]
        valid_data = signal_data[~np.isnan(signal_data)]

        if len(valid_data) == 0:
            return {
                "indicator_type": "range",
                "signal_name": signal_name,
                "result_status": "error",
                "result_value": None,
                "notes": "No valid data points",
            }

        out_of_range_count = 0
        violations = []

        if min_value is not None:
            below_min = valid_data < min_value
            out_of_range_count += np.sum(below_min)
            if np.any(below_min):
                violations.append(f"Below minimum ({min_value})")

        if max_value is not None:
            above_max = valid_data > max_value
            out_of_range_count += np.sum(above_max)
            if np.any(above_max):
                violations.append(f"Above maximum ({max_value})")

        total_points = len(valid_data)
        pass_rate = (total_points - out_of_range_count) / total_points * 100

        if out_of_range_count == 0:
            status = "pass"
        elif pass_rate >= 95:
            status = "warning"
        else:
            status = "fail"

        return {
            "indicator_type": "range",
            "signal_name": signal_name,
            "result_status": status,
            "result_value": {
                "min": float(np.min(valid_data)),
                "max": float(np.max(valid_data)),
                "mean": float(np.mean(valid_data)),
                "std": float(np.std(valid_data)),
                "out_of_range_count": int(out_of_range_count),
                "total_points": total_points,
                "pass_rate": round(pass_rate, 2),
            },
            "violations": violations,
            "unit": unit,
            "notes": f"Range check: {min_value} ~ {max_value}",
        }

    def calculate_statistics_indicator(
        self, signal_name: str, statistics: List[str] = None
    ) -> Dict[str, Any]:
        """
        计算统计指标

        Args:
            signal_name: 信号名称
            statistics: 要计算的统计量列表

        Returns:
            统计结果
        """
        if signal_name not in self.signals:
            raise IndicatorCalculationError(f"Signal '{signal_name}' not found")

        signal_data = self.signals[signal_name]
        valid_data = signal_data[~np.isnan(signal_data)]

        if statistics is None:
            statistics = ["min", "max", "mean", "std", "median"]

        result = {}
        for stat in statistics:
            if stat == "min":
                result["min"] = float(np.min(valid_data)) if len(valid_data) > 0 else None
            elif stat == "max":
                result["max"] = float(np.max(valid_data)) if len(valid_data) > 0 else None
            elif stat == "mean":
                result["mean"] = float(np.mean(valid_data)) if len(valid_data) > 0 else None
            elif stat == "std":
                result["std"] = float(np.std(valid_data)) if len(valid_data) > 0 else None
            elif stat == "median":
                result["median"] = float(np.median(valid_data)) if len(valid_data) > 0 else None
            elif stat == "variance":
                result["variance"] = float(np.var(valid_data)) if len(valid_data) > 0 else None
            elif stat == "count":
                result["count"] = len(valid_data)

        return {
            "indicator_type": "statistics",
            "signal_name": signal_name,
            "result_status": "pass",
            "result_value": result,
            "notes": f"Calculated statistics: {', '.join(statistics)}",
        }

    def calculate_logic_indicator(self, condition: str, description: str = None) -> Dict[str, Any]:
        """
        计算逻辑检查指标

        Args:
            condition: 逻辑条件表达式
            description: 描述

        Returns:
            检查结果
        """
        try:
            local_vars = {}
            for name, data in self.signals.items():
                if isinstance(data, np.ndarray):
                    local_vars[name] = data

            local_vars["np"] = np

            result = eval(condition, {"__builtins__": {}}, local_vars)
            result = np.array(result, dtype=bool)

            pass_count = np.sum(result)
            total_count = len(result)
            pass_rate = pass_count / total_count * 100 if total_count > 0 else 0

            if pass_rate == 100:
                status = "pass"
            elif pass_rate >= 95:
                status = "warning"
            else:
                status = "fail"

            return {
                "indicator_type": "logic",
                "condition": condition,
                "result_status": status,
                "result_value": {
                    "pass_count": int(pass_count),
                    "total_count": int(total_count),
                    "pass_rate": round(pass_rate, 2),
                },
                "description": description,
                "notes": f"Logic check: {condition}",
            }

        except Exception as e:
            return {
                "indicator_type": "logic",
                "condition": condition,
                "result_status": "error",
                "result_value": None,
                "error": str(e),
                "notes": f"Logic check failed: {str(e)}",
            }

    def detect_anomalies(
        self,
        signal_name: str,
        method: str = "threshold",
        threshold: Optional[float] = None,
        sigma: float = 3.0,
    ) -> Dict[str, Any]:
        """
        异常检测

        Args:
            signal_name: 信号名称
            method: 检测方法 ('threshold', 'sigma', 'iqr')
            threshold: 阈值（用于threshold方法）
            sigma: 标准差倍数（用于sigma方法）

        Returns:
            异常检测结果
        """
        if signal_name not in self.signals:
            raise AnalysisError(f"Signal '{signal_name}' not found")

        signal_data = self.signals[signal_name]
        valid_data = signal_data[~np.isnan(signal_data)]

        if len(valid_data) == 0:
            return {
                "signal_name": signal_name,
                "method": method,
                "result_status": "error",
                "anomaly_count": 0,
                "anomaly_indices": [],
                "notes": "No valid data points",
            }

        anomaly_mask = np.zeros(len(valid_data), dtype=bool)

        if method == "threshold" and threshold is not None:
            anomaly_mask = np.abs(valid_data) > threshold

        elif method == "sigma":
            mean = np.mean(valid_data)
            std = np.std(valid_data)
            lower_bound = mean - sigma * std
            upper_bound = mean + sigma * std
            anomaly_mask = (valid_data < lower_bound) | (valid_data > upper_bound)

        elif method == "iqr":
            q1 = np.percentile(valid_data, 25)
            q3 = np.percentile(valid_data, 75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            anomaly_mask = (valid_data < lower_bound) | (valid_data > upper_bound)

        anomaly_indices = np.where(anomaly_mask)[0].tolist()
        anomaly_count = len(anomaly_indices)

        if anomaly_count == 0:
            status = "pass"
        elif anomaly_count < len(valid_data) * 0.05:
            status = "warning"
        else:
            status = "fail"

        return {
            "signal_name": signal_name,
            "method": method,
            "result_status": status,
            "anomaly_count": anomaly_count,
            "anomaly_indices": anomaly_indices[:100],
            "anomaly_values": valid_data[anomaly_mask][:100].tolist(),
            "total_points": len(valid_data),
            "anomaly_rate": round(anomaly_count / len(valid_data) * 100, 2),
            "notes": f"Detected {anomaly_count} anomalies using {method} method",
        }

    def detect_step_response(
        self,
        trigger_signal: str,
        response_signal: str,
        trigger_condition: str = "change > 0",
        response_threshold: float = 0.95,
        max_time: float = None,
    ) -> Dict[str, Any]:
        """
        阶跃响应分析

        Args:
            trigger_signal: 触发信号
            response_signal: 响应信号
            trigger_condition: 触发条件
            response_threshold: 响应阈值（目标值的百分比）
            max_time: 最大响应时间

        Returns:
            响应分析结果
        """
        if trigger_signal not in self.signals or response_signal not in self.signals:
            raise AnalysisError("Required signals not found")

        trigger_data = self.signals[trigger_signal]
        response_data = self.signals[response_signal]

        time_data = None
        if self.time_column and self.time_column in self.signals:
            time_data = self.signals[self.time_column]
        else:
            time_data = np.arange(len(response_data))

        trigger_diff = np.diff(trigger_data)
        trigger_indices = np.where(trigger_diff != 0)[0]

        if len(trigger_indices) == 0:
            return {
                "indicator_type": "step_response",
                "result_status": "error",
                "notes": "No step change detected in trigger signal",
            }

        results = []
        for idx in trigger_indices[:10]:
            start_time = time_data[idx]
            initial_value = response_data[idx]

            target_value = (
                trigger_data[idx + 1] if idx + 1 < len(trigger_data) else trigger_data[idx]
            )
            threshold_value = initial_value + (target_value - initial_value) * response_threshold

            response_idx = None
            for i in range(idx, min(idx + 1000, len(response_data))):
                if response_data[i] >= threshold_value:
                    response_idx = i
                    break

            if response_idx is not None:
                response_time = time_data[response_idx] - start_time
                results.append(
                    {
                        "trigger_time": float(start_time),
                        "response_time": float(response_time),
                        "initial_value": float(initial_value),
                        "target_value": float(target_value),
                        "actual_value": float(response_data[response_idx]),
                    }
                )

        if not results:
            return {
                "indicator_type": "step_response",
                "result_status": "error",
                "notes": "No valid response detected",
            }

        avg_response_time = np.mean([r["response_time"] for r in results])

        return {
            "indicator_type": "step_response",
            "result_status": "pass",
            "result_value": {
                "average_response_time": float(avg_response_time),
                "response_count": len(results),
                "responses": results,
            },
            "notes": f"Average response time: {avg_response_time:.3f}s",
        }

    def run_full_analysis(
        self,
        indicators: List[Dict[str, Any]],
        signal_mappings: List[Dict[str, Any]] = None,
        custom_signals: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        执行完整分析

        Args:
            indicators: 指标配置列表
            signal_mappings: 信号映射配置
            custom_signals: 自定义信号配置

        Returns:
            完整分析结果
        """
        results = {
            "started_at": datetime.now().isoformat(),
            "indicators": [],
            "summary": {"total": 0, "pass": 0, "warning": 0, "fail": 0, "error": 0},
        }

        if signal_mappings:
            mapping_result = self.apply_signal_mappings(signal_mappings)
            results["signal_mappings"] = mapping_result

        if custom_signals:
            custom_result = self.calculate_custom_signals(custom_signals)
            results["custom_signals"] = custom_result

        for indicator in indicators:
            indicator_type = indicator.get("type", "statistics")
            indicator_id = indicator.get("id", f"ind_{len(results['indicators'])}")

            try:
                if indicator_type == "range":
                    result = self.calculate_range_indicator(
                        signal_name=indicator.get("signal"),
                        min_value=indicator.get("min"),
                        max_value=indicator.get("max"),
                        unit=indicator.get("unit"),
                    )
                elif indicator_type == "statistics":
                    result = self.calculate_statistics_indicator(
                        signal_name=indicator.get("signal"), statistics=indicator.get("statistics")
                    )
                elif indicator_type == "logic":
                    result = self.calculate_logic_indicator(
                        condition=indicator.get("condition"),
                        description=indicator.get("description"),
                    )
                elif indicator_type == "anomaly":
                    result = self.detect_anomalies(
                        signal_name=indicator.get("signal"),
                        method=indicator.get("method", "sigma"),
                        threshold=indicator.get("threshold"),
                        sigma=indicator.get("sigma", 3.0),
                    )
                elif indicator_type == "step_response":
                    result = self.detect_step_response(
                        trigger_signal=indicator.get("trigger_signal"),
                        response_signal=indicator.get("response_signal"),
                        trigger_condition=indicator.get("trigger_condition"),
                        response_threshold=indicator.get("response_threshold", 0.95),
                    )
                else:
                    result = {
                        "indicator_id": indicator_id,
                        "result_status": "error",
                        "notes": f"Unknown indicator type: {indicator_type}",
                    }

                result["indicator_id"] = indicator_id
                results["indicators"].append(result)

                status = result.get("result_status", "error")
                results["summary"]["total"] += 1
                results["summary"][status] = results["summary"].get(status, 0) + 1

            except Exception as e:
                results["indicators"].append(
                    {
                        "indicator_id": indicator_id,
                        "result_status": "error",
                        "error": str(e),
                        "notes": f"Analysis failed: {str(e)}",
                    }
                )
                results["summary"]["total"] += 1
                results["summary"]["error"] += 1

        results["completed_at"] = datetime.now().isoformat()

        return results

    def get_signal_data(self, signal_name: str) -> Optional[np.ndarray]:
        """获取信号数据"""
        return self.signals.get(signal_name)

    def get_all_signals(self) -> List[str]:
        """获取所有信号名称"""
        return list(self.signals.keys())

    def get_signal_summary(self) -> Dict[str, Dict[str, float]]:
        """获取所有信号的统计摘要"""
        summary = {}
        for name, data in self.signals.items():
            valid_data = data[~np.isnan(data)] if isinstance(data, np.ndarray) else np.array(data)
            if len(valid_data) > 0:
                summary[name] = {
                    "min": float(np.min(valid_data)),
                    "max": float(np.max(valid_data)),
                    "mean": float(np.mean(valid_data)),
                    "std": float(np.std(valid_data)),
                    "count": len(valid_data),
                }
        return summary


analysis_engine = AnalysisEngine()
