"""
报告生成API路由

提供报告生成和管理的REST API接口
"""

import logging
import os
import json
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.schemas import MessageResponse, ReportTemplate, Report
from app.models import (
    Project as ProjectModel,
    TestDataFile as TestDataFileModel,
    SignalMapping as SignalMappingModel,
    CustomSignal as CustomSignalModel,
    AnalysisResult as AnalysisResultModel,
    ReportTemplate as ReportTemplateModel,
    Report as ReportModel,
)
from app.services.report_engine import report_engine, ReportGenerationError
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class ReportGenerateOptions(BaseModel):
    template_id: Optional[int] = None
    report_type: str = "standard"
    format: str = "pdf"
    author: Optional[str] = None
    reviewer: Optional[str] = None
    approver: Optional[str] = None


class ReportTemplateCreate(BaseModel):
    template_name: str
    template_type: str
    oem_id: Optional[str] = None
    sections: List[dict] = []


@router.get("/report-templates")
def get_report_templates(db: Session = Depends(get_db)):
    """获取报告模板列表"""
    try:
        templates = db.query(ReportTemplateModel).all()

        if not templates:
            default_templates = _create_default_templates(db)
            templates = default_templates

        return [
            {
                "id": t.id,
                "template_name": t.template_name,
                "template_type": t.template_type,
                "oem_id": t.oem_id,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in templates
        ]

    except Exception as e:
        logger.error(f"Error retrieving templates: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve report templates",
        )


@router.post("/report-templates", response_model=ReportTemplate)
def create_report_template(template: ReportTemplateCreate, db: Session = Depends(get_db)):
    """创建报告模板"""
    try:
        db_template = ReportTemplateModel(
            template_name=template.template_name,
            template_type=template.template_type,
            oem_id=template.oem_id,
            sections=json.dumps(template.sections),
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)

        logger.info(
            f"Created report template: id={db_template.id}, name={db_template.template_name}"
        )

        return {
            "id": db_template.id,
            "template_name": db_template.template_name,
            "template_type": db_template.template_type,
            "oem_id": db_template.oem_id,
            "sections": template.sections,
            "created_at": db_template.created_at.isoformat() if db_template.created_at else None,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating template: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create report template",
        )


@router.post("/test-data/{test_data_id}/reports/generate")
def generate_report(
    test_data_id: int, options: ReportGenerateOptions, db: Session = Depends(get_db)
):
    """
    生成报告

    Args:
        test_data_id: 测试数据文件ID
        options: 报告生成选项
        db: 数据库会话

    Returns:
        报告信息
    """
    try:
        test_data = db.query(TestDataFileModel).filter(TestDataFileModel.id == test_data_id).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found",
            )

        project = db.query(ProjectModel).filter(ProjectModel.id == test_data.project_id).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {test_data.project_id} not found",
            )

        analysis_results = (
            db.query(AnalysisResultModel)
            .filter(AnalysisResultModel.test_data_file_id == test_data_id)
            .all()
        )

        signal_mappings = (
            db.query(SignalMappingModel).filter(SignalMappingModel.project_id == project.id).all()
        )

        report_data = _build_report_data(
            project=project,
            test_data=test_data,
            analysis_results=analysis_results,
            signal_mappings=signal_mappings,
            options=options,
        )

        report_dir = Path(settings.REPORT_DIR)
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_number = f"RPT-{project.id}-{test_data_id}-{timestamp}"

        file_ext = "pdf" if options.format == "pdf" else "docx"
        filename = f"{report_number}.{file_ext}"
        output_path = report_dir / filename

        if options.report_type == "traceability":
            report_engine.generate_traceability_report(
                report_data=report_data, output_path=str(output_path), format=options.format
            )
        else:
            report_engine.generate_standard_report(
                report_data=report_data, output_path=str(output_path), format=options.format
            )

        db_report = ReportModel(
            report_template_id=options.template_id or 1,
            test_data_file_id=test_data_id,
            project_id=project.id,
            report_type=options.report_type,
            report_number=report_number,
            report_date=datetime.now().strftime("%Y-%m-%d"),
            version="v1.0",
            status="completed",
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)

        logger.info(f"Generated report: id={db_report.id}, number={report_number}")

        return {
            "id": db_report.id,
            "report_number": report_number,
            "report_type": options.report_type,
            "format": options.format,
            "file_path": str(output_path),
            "file_name": filename,
            "created_at": db_report.created_at.isoformat() if db_report.created_at else None,
            "download_url": f"/api/reports/{db_report.id}/download?format={options.format}",
        }

    except ReportGenerationError as e:
        logger.error(f"Report generation error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}",
        )


@router.get("/reports/{report_id}/download")
def download_report(report_id: int, format: str = "pdf", db: Session = Depends(get_db)):
    """
    下载报告

    Args:
        report_id: 报告ID
        format: 下载格式
        db: 数据库会话

    Returns:
        报告文件
    """
    try:
        report = db.query(ReportModel).filter(ReportModel.id == report_id).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with id {report_id} not found",
            )

        report_dir = Path(settings.REPORT_DIR)

        file_ext = "pdf" if format == "pdf" else "docx"
        filename = f"{report.report_number}.{file_ext}"
        file_path = report_dir / filename

        if not file_path.exists():
            alt_ext = "docx" if format == "pdf" else "pdf"
            alt_filename = f"{report.report_number}.{alt_ext}"
            alt_path = report_dir / alt_filename

            if alt_path.exists():
                file_path = alt_path
                filename = alt_filename
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report file not found: {filename}",
                )

        media_type = (
            "application/pdf"
            if file_ext == "pdf"
            else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

        return FileResponse(path=str(file_path), filename=filename, media_type=media_type)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to download report"
        )


@router.get("/projects/{project_id}/reports")
def get_reports(project_id: int, db: Session = Depends(get_db)):
    """获取项目的报告列表"""
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        reports = (
            db.query(ReportModel)
            .filter(ReportModel.project_id == project_id)
            .order_by(ReportModel.created_at.desc())
            .all()
        )

        return [
            {
                "id": r.id,
                "report_number": r.report_number,
                "report_type": r.report_type,
                "report_date": r.report_date,
                "version": r.version,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reports
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving reports: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve reports"
        )


@router.delete("/reports/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    """删除报告"""
    try:
        report = db.query(ReportModel).filter(ReportModel.id == report_id).first()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report with id {report_id} not found",
            )

        report_dir = Path(settings.REPORT_DIR)
        for ext in ["pdf", "docx"]:
            filename = f"{report.report_number}.{ext}"
            file_path = report_dir / filename
            if file_path.exists():
                os.remove(file_path)

        db.delete(report)
        db.commit()

        logger.info(f"Deleted report: id={report_id}")

        return {"message": "Report deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting report: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete report"
        )


def _create_default_templates(db: Session) -> List[ReportTemplateModel]:
    """创建默认报告模板"""
    default_sections = [
        {"section_id": "cover", "section_name": "封面", "required": True},
        {"section_id": "toc", "section_name": "目录", "required": True},
        {"section_id": "summary", "section_name": "测试概述", "required": True},
        {"section_id": "results", "section_name": "测试结果汇总", "required": True},
        {"section_id": "indicators", "section_name": "关键指标分析", "required": True},
        {"section_id": "issues", "section_name": "问题列表", "required": False},
        {"section_id": "appendix", "section_name": "附录", "required": False},
    ]

    templates = []

    template1 = ReportTemplateModel(
        template_name="标准测试报告模板",
        template_type="full",
        oem_id=None,
        sections=json.dumps(default_sections),
    )
    db.add(template1)
    templates.append(template1)

    template2 = ReportTemplateModel(
        template_name="溯源报告模板",
        template_type="traceability",
        oem_id=None,
        sections=json.dumps(
            [
                {"section_id": "data_source", "section_name": "数据来源", "required": True},
                {"section_id": "signal_trace", "section_name": "信号溯源", "required": True},
                {"section_id": "detailed_results", "section_name": "详细结果", "required": True},
                {"section_id": "raw_data", "section_name": "原始数据引用", "required": True},
            ]
        ),
    )
    db.add(template2)
    templates.append(template2)

    db.commit()

    return templates


def _build_report_data(
    project: ProjectModel,
    test_data: TestDataFileModel,
    analysis_results: List[AnalysisResultModel],
    signal_mappings: List[SignalMappingModel],
    options: ReportGenerateOptions,
) -> dict:
    """构建报告数据"""
    indicators = []
    for r in analysis_results:
        try:
            result_value = json.loads(r.result_value) if r.result_value else {}
        except:
            result_value = {}

        indicators.append(
            {
                "indicator_id": r.indicator_id,
                "result_status": r.result_status,
                "result_value": result_value,
                "notes": r.notes,
            }
        )

    summary = {
        "total": len(indicators),
        "pass": len([i for i in indicators if i["result_status"] == "pass"]),
        "fail": len([i for i in indicators if i["result_status"] == "fail"]),
        "warning": len([i for i in indicators if i["result_status"] == "warning"]),
        "error": len([i for i in indicators if i["result_status"] == "error"]),
    }

    mappings_data = []
    for m in signal_mappings:
        mapping_dict = {
            "signal_alias": m.signal_alias,
            "data_source_signal": m.data_source_signal,
            "dbc_signal": m.dbc_signal,
            "source_file": test_data.file_name,
        }
        if m.unit_conversion_from_unit or m.unit_conversion_to_unit:
            mapping_dict["unit_conversion"] = {
                "from_unit": m.unit_conversion_from_unit or "",
                "to_unit": m.unit_conversion_to_unit or "",
                "formula": m.unit_conversion_formula or "x",
            }
        mappings_data.append(mapping_dict)

    report_data = {
        "project_name": project.name,
        "project_id": project.id,
        "report_number": f"RPT-{project.id}-{test_data.id}",
        "report_date": datetime.now().strftime("%Y-%m-%d"),
        "version": "v1.0",
        "author": options.author or "",
        "reviewer": options.reviewer or "",
        "approver": options.approver or "",
        "test_type": test_data.data_type,
        "test_date": test_data.uploaded_at.strftime("%Y-%m-%d") if test_data.uploaded_at else "",
        "software_version": "N/A",
        "hardware_version": "N/A",
        "dbc_version": "N/A",
        "test_purpose": f"验证{project.name}控制器功能是否符合设计要求。",
        "test_scope": "功能测试、性能测试",
        "summary": summary,
        "indicators": indicators,
        "issues": [],
        "data_sources": [
            {
                "file_name": test_data.file_name,
                "file_type": test_data.format,
                "file_size": f"{test_data.file_size / 1024 / 1024:.2f} MB",
                "import_time": test_data.uploaded_at.isoformat() if test_data.uploaded_at else "",
                "data_quality": "valid",
            }
        ],
        "signal_mappings": mappings_data,
        "provenance": {
            "test_data_id": test_data.id,
            "test_data_file": test_data.file_path,
            "analysis_time": datetime.now().isoformat(),
            "signal_count": len(signal_mappings),
        },
    }

    return report_data
