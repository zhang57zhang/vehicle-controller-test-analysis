"""
数据导入API路由

提供将解析后的数据导入到项目的功能。
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.file_parser import parse_file, FileParserError
from app.models import (
    Project as ProjectModel,
    TestDataFile as TestDataFileModel
)

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


class DataImportRequest(BaseModel):
    """数据导入请求"""
    project_id: int = Field(..., description="项目ID")
    file_id: str = Field(..., description="文件ID")
    file_type: str = Field(..., description="文件类型")
    file_path: str = Field(..., description="文件路径")
    data_type: str = Field(default="MANUAL", description="数据类型")
    description: Optional[str] = Field(None, description="描述")
    parse_options: Optional[Dict[str, Any]] = Field(None, description="解析选项")


class DataImportResponse(BaseModel):
    """数据导入响应"""
    success: bool
    message: str
    test_data_id: Optional[int] = None
    parsed_data: Optional[Dict[str, Any]] = None
    import_stats: Optional[Dict[str, Any]] = None


def create_test_data_file(
    db: Session,
    project_id: int,
    file_id: str,
    file_name: str,
    file_path: str,
    file_type: str,
    data_type: str,
    parsed_data: Dict[str, Any]
) -> TestDataFileModel:
    """
    创建测试数据文件记录

    Args:
        db: 数据库会话
        project_id: 项目ID
        file_id: 文件ID
        file_name: 文件名
        file_path: 文件路径
        file_type: 文件类型
        data_type: 数据类型
        parsed_data: 解析后的数据

    Returns:
        创建的测试数据文件记录

    Raises:
        HTTPException: 当数据库操作失败时
    """
    try:
        # 获取文件大小
        import os
        file_size = os.path.getsize(file_path)

        # 创建数据库记录
        db_file = TestDataFileModel(
            project_id=project_id,
            file_name=file_name,
            file_path=file_path,
            file_size=file_size,
            format=file_type,
            data_type=data_type
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        logger.info(f"Created test data file record: id={db_file.id}")
        return db_file

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating test data file record: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create test data file record"
        )


def generate_import_stats(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成导入统计信息

    Args:
        parsed_data: 解析后的数据

    Returns:
        导入统计信息字典
    """
    stats = {
        'file_type': parsed_data.get('file_type'),
        'total_records': 0,
        'fields_count': 0,
        'data_size': 0
    }

    if parsed_data.get('file_type') in ['csv', 'excel']:
        stats['total_records'] = parsed_data.get('row_count', 0)
        stats['fields_count'] = len(parsed_data.get('columns', []))
        stats['data_size'] = len(str(parsed_data.get('data', [])))
    elif parsed_data.get('file_type') == 'mat':
        stats['total_records'] = len(parsed_data.get('variables', []))
        stats['fields_count'] = len(parsed_data.get('variables', []))
        stats['data_size'] = len(str(parsed_data.get('data', {})))
    elif parsed_data.get('file_type') == 'log':
        stats['total_records'] = parsed_data.get('message_count', 0)
        stats['fields_count'] = len(parsed_data.get('arbitration_ids', []))
        stats['data_size'] = len(str(parsed_data.get('messages', [])))
    elif parsed_data.get('file_type') == 'dbc':
        stats['total_records'] = parsed_data.get('messages_count', 0)
        stats['fields_count'] = sum(len(m.get('signals', [])) for m in parsed_data.get('messages', []))
        stats['data_size'] = len(str(parsed_data.get('messages', [])))

    return stats


@router.post("/api/data/import", response_model=DataImportResponse, status_code=status.HTTP_201_CREATED)
async def import_data(
    request: DataImportRequest,
    db: Session = Depends(get_db)
) -> DataImportResponse:
    """
    导入数据到项目

    支持的文件类型：CSV、Excel、MATLAB .mat、DBC、Vector CAN log

    Args:
        request: 数据导入请求
        db: 数据库会话

    Returns:
        数据导入响应

    Raises:
        HTTPException 400: 请求数据验证失败时
        HTTPException 404: 项目不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        # 验证项目存在
        project = db.query(ProjectModel).filter(ProjectModel.id == request.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {request.project_id} not found"
            )

        # 解析文件
        parse_options = request.parse_options or {}
        try:
            parsed_data = parse_file(request.file_path, request.file_type, **parse_options)
        except FileParserError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File parsing failed: {str(e)}"
            )

        # 创建测试数据文件记录
        file_name = request.file_path.split('\\')[-1] if '\\' in request.file_path else request.file_path.split('/')[-1]
        test_data_file = create_test_data_file(
            db=db,
            project_id=request.project_id,
            file_id=request.file_id,
            file_name=file_name,
            file_path=request.file_path,
            file_type=request.file_type,
            data_type=request.data_type,
            parsed_data=parsed_data
        )

        # 生成导入统计信息
        import_stats = generate_import_stats(parsed_data)

        logger.info(
            f"Successfully imported data: project_id={request.project_id}, "
            f"test_data_id={test_data_file.id}, file_type={request.file_type}"
        )

        return DataImportResponse(
            success=True,
            message=f"Data imported successfully. {import_stats['total_records']} records processed.",
            test_data_id=test_data_file.id,
            parsed_data=parsed_data,
            import_stats=import_stats
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import data: {str(e)}"
        )


@router.post("/api/data/parse", status_code=status.HTTP_200_OK)
async def parse_file_only(
    file_path: str,
    file_type: str,
    parse_options: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    仅解析文件，不导入数据库

    用于预览文件内容，验证文件格式是否正确。

    Args:
        file_path: 文件路径
        file_type: 文件类型
        parse_options: 解析选项（可选）

    Returns:
        解析后的数据

    Raises:
        HTTPException 400: 文件解析失败时
        HTTPException 404: 文件不存在时
    """
    try:
        # 验证文件存在
        from pathlib import Path
        if not Path(file_path).exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {file_path}"
            )

        # 解析文件
        parse_options = parse_options or {}
        try:
            parsed_data = parse_file(file_path, file_type, **parse_options)
        except FileParserError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File parsing failed: {str(e)}"
            )

        # 生成统计信息
        import_stats = generate_import_stats(parsed_data)

        return {
            'success': True,
            'parsed_data': parsed_data,
            'import_stats': import_stats
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse file: {str(e)}"
        )


@router.get("/api/data/import-stats/{test_data_id}", status_code=status.HTTP_200_OK)
async def get_import_stats(
    test_data_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取数据导入统计信息

    Args:
        test_data_id: 测试数据文件ID
        db: 数据库会话

    Returns:
        导入统计信息

    Raises:
        HTTPException 404: 测试数据文件不存在时
    """
    try:
        # 查询测试数据文件
        test_data = db.query(TestDataFileModel).filter(
            TestDataFileModel.id == test_data_id
        ).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found"
            )

        # 获取关联的项目信息
        project = db.query(ProjectModel).filter(
            ProjectModel.id == test_data.project_id
        ).first()

        return {
            'test_data_id': test_data.id,
            'project_id': test_data.project_id,
            'project_name': project.name if project else None,
            'file_name': test_data.file_name,
            'file_type': test_data.format,
            'data_type': test_data.data_type,
            'file_size': test_data.file_size,
            'uploaded_at': test_data.uploaded_at.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting import stats for {test_data_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get import stats"
        )
