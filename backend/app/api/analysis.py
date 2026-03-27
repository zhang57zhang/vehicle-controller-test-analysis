"""
数据分析API路由

提供数据分析功能的REST API接口
"""

import logging
import json
import numpy as np
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.schemas import MessageResponse, AnalysisRequest
from app.models import (
    TestDataFile as TestDataFileModel,
    SignalMapping as SignalMappingModel,
    CustomSignal as CustomSignalModel,
    AnalysisResult as AnalysisResultModel,
    Project as ProjectModel,
)
from app.services.analysis_engine import AnalysisEngine, AnalysisError
from app.services.time_sync_service import time_sync_service, TimeSyncError
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class IndicatorConfig(BaseModel):
    id: str
    type: str
    signal: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    unit: Optional[str] = None
    statistics: Optional[List[str]] = None
    condition: Optional[str] = None
    description: Optional[str] = None
    method: Optional[str] = None
    threshold: Optional[float] = None
    sigma: Optional[float] = None
    trigger_signal: Optional[str] = None
    response_signal: Optional[str] = None
    trigger_condition: Optional[str] = None
    response_threshold: Optional[float] = None


class AnalysisOptions(BaseModel):
    time_sync: Optional[dict] = None
    indicators: Optional[List[IndicatorConfig]] = None
    use_project_mappings: Optional[bool] = True
    use_project_custom_signals: Optional[bool] = True


def get_file_type(filename: str) -> str:
    """根据文件扩展名获取文件类型"""
    from pathlib import Path

    ext = Path(filename).suffix.lower()
    type_map = {
        ".mat": "mat",
        ".csv": "csv",
        ".xlsx": "excel",
        ".xls": "excel",
        ".log": "log",
        ".blf": "log",
        ".asc": "log",
    }
    return type_map.get(ext, "csv")


@router.post("/test-data/{test_data_id}/analyze")
def execute_analysis(test_data_id: int, options: AnalysisOptions, db: Session = Depends(get_db)):
    """
    执行数据分析

    Args:
        test_data_id: 测试数据文件ID
        options: 分析选项
        db: 数据库会话

    Returns:
        分析结果
    """
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        engine = AnalysisEngine()

        file_type = get_file_type(test_data.file_name)
        load_result = engine.load_data(test_data.file_path, file_type)
        logger.info(f"Loaded test data: {load_result}")

        signal_mappings = []
        custom_signals = []

        if options.use_project_mappings:
            mappings = (
                db.query(SignalMappingModel)
                .filter(SignalMappingModel.project_id == test_data.project_id)
                .all()
            )

            for m in mappings:
                mapping_dict = {
                    "signal_alias": m.signal_alias,
                    "dbc_signal": m.dbc_signal,
                    "data_source_signal": m.data_source_signal,
                }
                if m.unit_conversion_from_unit or m.unit_conversion_to_unit:
                    mapping_dict["unit_conversion"] = {
                        "from_unit": m.unit_conversion_from_unit or "",
                        "to_unit": m.unit_conversion_to_unit or "",
                        "formula": m.unit_conversion_formula or "x",
                    }
                signal_mappings.append(mapping_dict)

        if options.use_project_custom_signals:
            customs = (
                db.query(CustomSignalModel)
                .filter(CustomSignalModel.project_id == test_data.project_id)
                .all()
            )

            for c in customs:
                input_signals = []
                if c.input_signals:
                    try:
                        input_signals = json.loads(c.input_signals)
                    except:
                        input_signals = c.input_signals.split(",")

                custom_signals.append(
                    {
                        "signal_alias": c.signal_alias,
                        "calculation": c.calculation,
                        "input_signals": input_signals,
                    }
                )

        indicators = []
        if options.indicators:
            indicators = [ind.model_dump() for ind in options.indicators]

        if not indicators:
            signals = engine.get_all_signals()
            for sig in signals[:10]:
                indicators.append(
                    {
                        "id": f"stat_{sig}",
                        "type": "statistics",
                        "signal": sig,
                        "statistics": ["min", "max", "mean", "std"],
                    }
                )

        results = engine.run_full_analysis(
            indicators=indicators,
            signal_mappings=signal_mappings if signal_mappings else None,
            custom_signals=custom_signals if custom_signals else None,
        )

        for indicator_result in results.get("indicators", []):
            db_result = AnalysisResultModel(
                test_data_file_id=test_data_id,
                indicator_id=indicator_result.get("indicator_id", "unknown"),
                result_value=json.dumps(indicator_result.get("result_value", {})),
                result_status=indicator_result.get("result_status", "error"),
                notes=indicator_result.get("notes", ""),
            )
            db.add(db_result)

        db.commit()

        signal_summary = engine.get_signal_summary()

        return {
            "status": "success",
            "test_data_id": test_data_id,
            "signals_loaded": len(engine.get_all_signals()),
            "signal_summary": signal_summary,
            "analysis_results": results,
        }

    except AnalysisError as e:
        logger.error(f"Analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute analysis: {str(e)}",
        )


@router.get("/test-data/{test_data_id}/analysis-results")
def get_analysis_results(test_data_id: int, db: Session = Depends(get_db)):
    """
    获取分析结果

    Args:
        test_data_id: 测试数据文件ID
        db: 数据库会话

    Returns:
        分析结果列表
    """
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        results = (
            db.query(AnalysisResultModel)
            .filter(AnalysisResultModel.test_data_file_id == test_data_id)
            .order_by(AnalysisResultModel.calculated_at.desc())
            .all()
        )

        return [
            {
                "id": r.id,
                "indicator_id": r.indicator_id,
                "result_value": json.loads(r.result_value) if r.result_value else {},
                "result_status": r.result_status,
                "notes": r.notes,
                "calculated_at": r.calculated_at.isoformat() if r.calculated_at else None,
            }
            for r in results
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving analysis results: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analysis results",
        )


@router.get("/test-data/{test_data_id}/signals")
def get_available_signals(test_data_id: int, db: Session = Depends(get_db)):
    """
    获取测试数据中的可用信号列表

    Args:
        test_data_id: 测试数据文件ID
        db: 数据库会话

    Returns:
        信号列表和摘要
    """
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        engine = AnalysisEngine()
        file_type = get_file_type(test_data.file_name)
        engine.load_data(test_data.file_path, file_type)

        signals = engine.get_all_signals()
        summary = engine.get_signal_summary()

        return {
            "test_data_id": test_data_id,
            "signals": signals,
            "signal_count": len(signals),
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"Error getting signals: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get signals: {str(e)}",
        )


@router.post("/test-data/{test_data_id}/analyze/quick")
def quick_analysis(test_data_id: int, db: Session = Depends(get_db)):
    """
    快速分析 - 自动执行基础统计分析

    Args:
        test_data_id: 测试数据文件ID
        db: 数据库会话

    Returns:
        快速分析结果
    """
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        engine = AnalysisEngine()
        file_type = get_file_type(test_data.file_name)
        engine.load_data(test_data.file_path, file_type)

        signals = engine.get_all_signals()
        summary = engine.get_signal_summary()

        anomaly_results = []
        for sig in signals[:5]:
            try:
                anomaly = engine.detect_anomalies(sig, method="sigma", sigma=3.0)
                anomaly_results.append(
                    {
                        "signal": sig,
                        "status": anomaly.get("result_status"),
                        "anomaly_count": anomaly.get("anomaly_count", 0),
                        "anomaly_rate": anomaly.get("anomaly_rate", 0),
                    }
                )
            except:
                pass

        return {
            "status": "success",
            "test_data_id": test_data_id,
            "file_name": test_data.file_name,
            "file_type": file_type,
            "signal_count": len(signals),
            "signals": signals,
            "statistics": summary,
            "anomaly_detection": anomaly_results,
        }

    except Exception as e:
        logger.error(f"Error in quick analysis: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quick analysis failed: {str(e)}",
        )


class TimeSyncOptions(BaseModel):
    target_sampling_rate: Optional[float] = None
    interpolation_method: Optional[str] = "linear"
    sync_events: Optional[List[dict]] = None


@router.post("/test-data/{test_data_id}/time-sync")
def apply_time_sync(test_data_id: int, options: TimeSyncOptions, db: Session = Depends(get_db)):
    """
    应用时间同步和重采样

    Args:
        test_data_id: 测试数据文件ID
        options: 时间同步选项
        db: 数据库会话

    Returns:
        时间同步结果
    """
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        engine = AnalysisEngine()
        file_type = get_file_type(test_data.file_name)
        engine.load_data(test_data.file_path, file_type)

        signals = engine.signals
        time_info = time_sync_service.get_time_info(signals)

        resampled_data, resample_metadata = time_sync_service.resample_data(
            data=signals,
            target_sampling_rate=options.target_sampling_rate,
            interpolation_method=options.interpolation_method,
        )

        quality_result = time_sync_service.evaluate_sync_quality(
            original_data=signals, resampled_data=resampled_data
        )

        return {
            "status": "success",
            "test_data_id": test_data_id,
            "original_time_info": time_info,
            "resample_metadata": resample_metadata,
            "quality_evaluation": quality_result,
            "resampled_signals": list(resampled_data.keys()),
        }

    except TimeSyncError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error applying time sync: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply time sync: {str(e)}",
        )


@router.post("/test-data/merge")
def merge_multiple_data(
    test_data_ids: List[int], options: TimeSyncOptions, db: Session = Depends(get_db)
):
    """
    合并多个测试数据文件

    Args:
        test_data_ids: 测试数据文件ID列表
        options: 时间同步选项
        db: 数据库会话

    Returns:
        合并后的数据信息
    """
    try:
        if len(test_data_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 test data files are required for merging",
            )

        data_sources = []
        for td_id in test_data_ids:
            test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == td_id).first()

            if not test_data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Test data file with id {td_id} not found",
                )

            engine = AnalysisEngine()
            file_type = get_file_type(test_data.file_name)
            engine.load_data(test_data.file_path, file_type)

            data_sources.append(engine.signals)

        merged_data, merge_metadata = time_sync_service.merge_data_sources(
            data_sources=data_sources,
            target_sampling_rate=options.target_sampling_rate,
            interpolation_method=options.interpolation_method,
        )

        return {
            "status": "success",
            "merged_signal_count": len(merged_data) - 1,
            "signals": list(merged_data.keys()),
            "metadata": merge_metadata,
        }

    except TimeSyncError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error merging data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge data: {str(e)}",
        )


class SignalTimeSeriesRequest(BaseModel):
    signal_names: List[str]
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    max_points: Optional[int] = 5000


@router.post("/test-data/{test_data_id}/signal-timeseries")
def get_signal_timeseries(
    test_data_id: int, request: SignalTimeSeriesRequest, db: Session = Depends(get_db)
):
    """
    获取信号的时序数据用于示波器显示

    Args:
        test_data_id: 测试数据文件ID
        request: 信号时序请求

    Returns:
        信号时序数据
    """
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        engine = AnalysisEngine()
        file_type = get_file_type(test_data.file_name)
        engine.load_data(test_data.file_path, file_type)

        if not engine.signals:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No signals found in the test data file",
            )

        time_data = None
        if engine.time_column and engine.time_column in engine.signals:
            time_data = engine.signals[engine.time_column]
        else:
            max_len = max(len(v) for v in engine.signals.values()) if engine.signals else 0
            time_data = np.arange(max_len)

        if not request.signal_names:
            request.signal_names = list(engine.signals.keys())[:50]

        result_data = {"time": time_data.tolist(), "signals": {}, "statistics": {}}

        for signal_name in request.signal_names:
            if signal_name in engine.signals:
                signal_data = engine.signals[signal_name]

                if not isinstance(signal_data, np.ndarray):
                    signal_data = np.array(signal_data)

                if len(signal_data) == 0:
                    continue

                valid_mask = np.ones(len(signal_data), dtype=bool)
                if request.start_time is not None and len(time_data) == len(signal_data):
                    valid_mask &= time_data >= request.start_time
                if request.end_time is not None and len(time_data) == len(signal_data):
                    valid_mask &= time_data <= request.end_time

                filtered_time = (
                    time_data[valid_mask] if len(time_data) == len(valid_mask) else time_data
                )
                filtered_data = signal_data[valid_mask]

                if request.max_points and len(filtered_data) > request.max_points:
                    step = max(1, len(filtered_data) // request.max_points)
                    filtered_data = filtered_data[::step]
                    filtered_time = filtered_time[::step]

                result_data["signals"][signal_name] = filtered_data.tolist()

                try:
                    numeric_data = signal_data.astype(float)
                    valid_values = numeric_data[~np.isnan(numeric_data)]
                    if len(valid_values) > 0:
                        result_data["statistics"][signal_name] = {
                            "min": float(np.min(valid_values)),
                            "max": float(np.max(valid_values)),
                            "mean": float(np.mean(valid_values)),
                            "std": float(np.std(valid_values)),
                            "count": len(valid_values),
                        }
                except (ValueError, TypeError):
                    pass

        if result_data["signals"]:
            first_signal_len = len(list(result_data["signals"].values())[0])
            result_data["time"] = result_data["time"][:first_signal_len]

        return {"status": "success", "test_data_id": test_data_id, "data": result_data}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting signal timeseries: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get signal timeseries: {str(e)}",
        )


@router.get("/test-data/{test_data_id}/time-info")
def get_time_info(test_data_id: int, db: Session = Depends(get_db)):
    """
    获取测试数据的时间信息

    Args:
        test_data_id: 测试数据文件ID
        db: 数据库会话

    Returns:
        时间信息
    """
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        engine = AnalysisEngine()
        file_type = get_file_type(test_data.file_name)
        engine.load_data(test_data.file_path, file_type)

        time_info = time_sync_service.get_time_info(engine.signals)

        return {"status": "success", "test_data_id": test_data_id, "time_info": time_info}

    except Exception as e:
        logger.error(f"Error getting time info: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get time info: {str(e)}",
        )
