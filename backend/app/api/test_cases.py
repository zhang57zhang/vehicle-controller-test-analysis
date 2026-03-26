"""
测试用例API路由

提供测试用例导入、查询和导出功能
"""

import logging
import os
import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.schemas import MessageResponse
from app.models import (
    Project as ProjectModel,
    TestCase as TestCaseModel,
    TestResult as TestResultModel,
    TestDataFile as TestDataFileModel,
)
from app.services.test_case_importer import test_case_importer, TestCaseImportError
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class TestCaseCreate(BaseModel):
    tc_id: str
    tc_name: str
    test_phase: str
    pre_condition: Optional[str] = None
    test_steps: Optional[str] = None
    expected_result: Optional[str] = None
    priority: Optional[str] = "Medium"


class TestResultCreate(BaseModel):
    tc_id: str
    result: str
    signal_name: Optional[str] = None
    measured_value: Optional[str] = None
    expected_min: Optional[str] = None
    expected_max: Optional[str] = None
    result_judgment: Optional[str] = None
    notes: Optional[str] = None


@router.post("/projects/{project_id}/test-cases/import")
async def import_test_cases(
    project_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)
):
    """
    导入测试用例Excel

    Args:
        project_id: 项目ID
        file: 上传的Excel文件
        db: 数据库会话

    Returns:
        导入结果
    """
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        if not file.filename.endswith((".xlsx", ".xls")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only Excel files (.xlsx, .xls) are supported",
            )

        temp_dir = Path(settings.TEMP_DIR)
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_path = temp_dir / f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"

        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        try:
            parse_result = test_case_importer.parse_excel(str(temp_path))
        finally:
            if temp_path.exists():
                os.remove(temp_path)

        test_cases = parse_result.get("test_cases", [])
        imported_ids = []
        errors = []

        for tc_data in test_cases:
            try:
                existing = (
                    db.query(TestCaseModel).filter(TestCaseModel.tc_id == tc_data["tc_id"]).first()
                )

                if existing:
                    existing.tc_name = tc_data["tc_name"]
                    existing.test_phase = tc_data["test_phase"]
                    existing.pre_condition = tc_data.get("pre_condition")
                    existing.test_steps = tc_data.get("test_steps")
                    existing.expected_result = tc_data.get("expected_result")
                    existing.priority = tc_data.get("priority", "Medium")
                    existing.version = tc_data.get("version", "1.0")
                    existing.author = tc_data.get("author")
                    existing.status = "active"
                    existing.updated_at = datetime.now()

                    db.commit()
                    imported_ids.append(existing.id)
                else:
                    new_tc = TestCaseModel(
                        project_id=project_id,
                        tc_id=tc_data["tc_id"],
                        tc_name=tc_data["tc_name"],
                        test_phase=tc_data["test_phase"],
                        pre_condition=tc_data.get("pre_condition"),
                        test_steps=tc_data.get("test_steps"),
                        expected_result=tc_data.get("expected_result"),
                        priority=tc_data.get("priority", "Medium"),
                        version=tc_data.get("version", "1.0"),
                        author=tc_data.get("author"),
                        status="active",
                    )
                    db.add(new_tc)
                    db.commit()
                    db.refresh(new_tc)
                    imported_ids.append(new_tc.id)

            except Exception as e:
                errors.append(f"TC_ID {tc_data.get('tc_id', 'unknown')}: {str(e)}")

        logger.info(f"Imported {len(imported_ids)} test cases for project {project_id}")

        return {
            "status": "success",
            "project_id": project_id,
            "total_rows": parse_result.get("total_rows", 0),
            "imported_count": len(imported_ids),
            "imported_ids": imported_ids,
            "error_count": len(errors),
            "errors": errors[:10],
        }

    except TestCaseImportError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing test cases: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import test cases: {str(e)}",
        )


@router.get("/projects/{project_id}/test-cases")
def get_test_cases(
    project_id: int,
    test_phase: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    获取测试用例列表

    Args:
        project_id: 项目ID
        test_phase: 测试阶段过滤
        priority: 优先级过滤
        skip: 分页偏移
        limit: 分页限制
        db: 数据库会话

    Returns:
        测试用例列表
    """
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        query = db.query(TestCaseModel).filter(TestCaseModel.project_id == project_id)

        if test_phase:
            query = query.filter(TestCaseModel.test_phase == test_phase)

        if priority:
            query = query.filter(TestCaseModel.priority == priority)

        test_cases = query.order_by(TestCaseModel.created_at.desc()).offset(skip).limit(limit).all()

        return [
            {
                "id": tc.id,
                "project_id": tc.project_id,
                "tc_id": tc.tc_id,
                "tc_name": tc.tc_name,
                "test_phase": tc.test_phase,
                "pre_condition": tc.pre_condition,
                "test_steps": tc.test_steps,
                "expected_result": tc.expected_result,
                "priority": tc.priority,
                "version": tc.version,
                "author": tc.author,
                "status": tc.status,
                "created_at": tc.created_at.isoformat() if tc.created_at else None,
            }
            for tc in test_cases
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving test cases: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test cases",
        )


@router.get("/test-cases/{test_case_id}")
def get_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """获取单个测试用例详情"""
    try:
        tc = db.query(TestCaseModel).filter(TestCaseModel.id == test_case_id).first()

        if not tc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test case with id {test_case_id} not found",
            )

        return {
            "id": tc.id,
            "project_id": tc.project_id,
            "tc_id": tc.tc_id,
            "tc_name": tc.tc_name,
            "test_phase": tc.test_phase,
            "pre_condition": tc.pre_condition,
            "test_steps": tc.test_steps,
            "expected_result": tc.expected_result,
            "priority": tc.priority,
            "version": tc.version,
            "author": tc.author,
            "status": tc.status,
            "created_at": tc.created_at.isoformat() if tc.created_at else None,
            "updated_at": tc.updated_at.isoformat() if tc.updated_at else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving test case: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve test case"
        )


@router.post("/projects/{project_id}/test-cases")
def create_test_case(project_id: int, tc: TestCaseCreate, db: Session = Depends(get_db)):
    """创建测试用例"""
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        existing = db.query(TestCaseModel).filter(TestCaseModel.tc_id == tc.tc_id).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Test case with TC_ID '{tc.tc_id}' already exists",
            )

        new_tc = TestCaseModel(
            project_id=project_id,
            tc_id=tc.tc_id,
            tc_name=tc.tc_name,
            test_phase=tc.test_phase,
            pre_condition=tc.pre_condition,
            test_steps=tc.test_steps,
            expected_result=tc.expected_result,
            priority=tc.priority or "Medium",
            status="active",
        )

        db.add(new_tc)
        db.commit()
        db.refresh(new_tc)

        logger.info(f"Created test case: id={new_tc.id}, tc_id={new_tc.tc_id}")

        return {
            "id": new_tc.id,
            "tc_id": new_tc.tc_id,
            "tc_name": new_tc.tc_name,
            "status": "created",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test case: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create test case"
        )


@router.delete("/test-cases/{test_case_id}")
def delete_test_case(test_case_id: int, db: Session = Depends(get_db)):
    """删除测试用例"""
    try:
        tc = db.query(TestCaseModel).filter(TestCaseModel.id == test_case_id).first()

        if not tc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test case with id {test_case_id} not found",
            )

        db.delete(tc)
        db.commit()

        logger.info(f"Deleted test case: id={test_case_id}")

        return {"message": "Test case deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting test case: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete test case"
        )


@router.get("/test-cases/template")
def download_template():
    """下载测试用例导入模板"""
    try:
        temp_dir = Path(settings.TEMP_DIR)
        temp_dir.mkdir(parents=True, exist_ok=True)

        template_path = temp_dir / "test_case_template.xlsx"
        test_case_importer.generate_template(str(template_path))

        return FileResponse(
            path=str(template_path),
            filename="test_case_template.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        logger.error(f"Error generating template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate template"
        )


@router.post("/test-data/{test_data_id}/test-results")
def create_test_result(test_data_id: int, result: TestResultCreate, db: Session = Depends(get_db)):
    """创建测试结果"""
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        tc = db.query(TestCaseModel).filter(TestCaseModel.tc_id == result.tc_id).first()

        new_result = TestResultModel(
            test_data_file_id=test_data_id,
            test_case_id=tc.id if tc else None,
            tc_id=result.tc_id,
            tc_name=tc.tc_name if tc else result.tc_id,
            test_steps=tc.test_steps if tc else None,
            expected_result=tc.expected_result if tc else None,
            result=result.result,
            signal_name=result.signal_name,
            measured_value=result.measured_value,
            expected_min=result.expected_min,
            expected_max=result.expected_max,
            result_judgment=result.result_judgment,
            notes=result.notes,
        )

        db.add(new_result)
        db.commit()
        db.refresh(new_result)

        logger.info(f"Created test result: id={new_result.id}, tc_id={result.tc_id}")

        return {
            "id": new_result.id,
            "tc_id": result.tc_id,
            "result": result.result,
            "status": "created",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test result: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create test result"
        )


@router.get("/test-data/{test_data_id}/test-results")
def get_test_results(test_data_id: int, db: Session = Depends(get_db)):
    """获取测试结果列表"""
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        results = (
            db.query(TestResultModel)
            .filter(TestResultModel.test_data_file_id == test_data_id)
            .order_by(TestResultModel.executed_at.desc())
            .all()
        )

        return [
            {
                "id": r.id,
                "tc_id": r.tc_id,
                "tc_name": r.tc_name,
                "result": r.result,
                "signal_name": r.signal_name,
                "measured_value": r.measured_value,
                "expected_min": r.expected_min,
                "expected_max": r.expected_max,
                "result_judgment": r.result_judgment,
                "notes": r.notes,
                "executed_at": r.executed_at.isoformat() if r.executed_at else None,
                "executed_by": r.executed_by,
            }
            for r in results
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving test results: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test results",
        )


@router.get("/test-data/{test_data_id}/results/export")
def export_test_results(test_data_id: int, format: str = "excel", db: Session = Depends(get_db)):
    """
    导出测试结果

    Args:
        test_data_id: 测试数据文件ID
        format: 导出格式 ('excel' 或 'csv')
        db: 数据库会话

    Returns:
        导出的文件
    """
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        results = (
            db.query(TestResultModel)
            .filter(TestResultModel.test_data_file_id == test_data_id)
            .all()
        )

        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No test results found for this test data",
            )

        results_data = [
            {
                "tc_id": r.tc_id,
                "tc_name": r.tc_name,
                "test_phase": "",
                "result": r.result,
                "signal_name": r.signal_name or "",
                "measured_value": r.measured_value or "",
                "expected_min": r.expected_min or "",
                "expected_max": r.expected_max or "",
                "pass_fail": "PASS" if r.result == "PASS" else "FAIL",
                "notes": r.notes or "",
                "executed_at": r.executed_at.strftime("%Y-%m-%d %H:%M:%S") if r.executed_at else "",
            }
            for r in results
        ]

        temp_dir = Path(settings.TEMP_DIR)
        temp_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "csv":
            filename = f"test_results_{test_data_id}_{timestamp}.csv"
            output_path = temp_dir / filename
            test_case_importer.export_test_results(results_data, str(output_path), "csv")
            media_type = "text/csv"
        else:
            filename = f"test_results_{test_data_id}_{timestamp}.xlsx"
            output_path = temp_dir / filename
            test_case_importer.export_test_results(results_data, str(output_path), "excel")
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        return FileResponse(path=str(output_path), filename=filename, media_type=media_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting test results: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export test results: {str(e)}",
        )
