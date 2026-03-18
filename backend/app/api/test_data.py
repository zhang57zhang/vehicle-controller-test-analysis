"""
测试数据API路由

提供测试数据文件的上传、查询、删除等功能。
支持多种文件格式：MAT、CSV、Excel、CAN日志等。
"""
import os
import logging
import aiofiles
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.schemas import TestDataFile, MessageResponse
from app.models import (
    Project as ProjectModel,
    TestDataFile as TestDataFileModel
)

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 支持的文件类型映射
FILE_TYPE_MAPPING = {
    '.mat': 'mat',
    '.csv': 'csv',
    '.xlsx': 'excel',
    '.xls': 'excel',
    '.log': 'log',
    '.blf': 'log',
    '.asc': 'log',
    '.xml': 'xml',
    '.json': 'json'
}

# 支持的数据类型
VALID_DATA_TYPES = {
    'MIL', 'HIL', 'DVP', 'VEHICLE', 'MANUAL', 'AUTO'
}


def get_file_format(filename: str) -> str:
    """
    根据文件扩展名获取文件格式

    Args:
        filename: 文件名

    Returns:
        文件格式字符串

    Raises:
        ValueError: 当文件格式不支持时
    """
    ext = Path(filename).suffix.lower()
    if ext not in FILE_TYPE_MAPPING:
        raise ValueError(f"Unsupported file format: {ext}")
    return FILE_TYPE_MAPPING[ext]


def validate_file_size(file_size: int) -> None:
    """
    验证文件大小是否在允许范围内

    Args:
        file_size: 文件大小（字节）

    Raises:
        ValueError: 当文件大小超过限制时
    """
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise ValueError(
            f"File size {file_size} exceeds maximum allowed size {settings.MAX_UPLOAD_SIZE}"
        )


def validate_data_type(data_type: str) -> None:
    """
    验证数据类型是否有效

    Args:
        data_type: 数据类型

    Raises:
        ValueError: 当数据类型无效时
    """
    if data_type not in VALID_DATA_TYPES:
        raise ValueError(
            f"Invalid data type: {data_type}. Must be one of {VALID_DATA_TYPES}"
        )


async def save_uploaded_file(
    project_id: int,
    file: UploadFile,
    file_size: int
) -> str:
    """
    保存上传的文件

    Args:
        project_id: 项目ID
        file: 上传的文件对象
        file_size: 文件大小

    Returns:
        保存的文件路径

    Raises:
        HTTPException: 当文件保存失败时
    """
    try:
        # 创建项目目录
        project_dir = Path(settings.UPLOAD_DIR) / f"project_{project_id}"
        project_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名（添加时间戳避免冲突）
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = Path(file.filename).suffix
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = project_dir / safe_filename

        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        logger.info(f"Saved file: {file_path} ({file_size} bytes)")
        return str(file_path)

    except Exception as e:
        logger.error(f"Error saving file {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


@router.post(
    "/projects/{project_id}/test-data/upload",
    response_model=TestDataFile,
    status_code=status.HTTP_201_CREATED
)
async def upload_test_data(
    project_id: int,
    file: UploadFile = File(...),
    data_type: str = "MANUAL",
    db: Session = Depends(get_db)
) -> TestDataFile:
    """
    上传测试数据文件

    Args:
        project_id: 项目ID
        file: 上传的文件
        data_type: 数据类型（MIL/HIL/DVP/VEHICLE/MANUAL/AUTO）
        db: 数据库会话

    Returns:
        创建的测试数据文件记录

    Raises:
        HTTPException 400: 文件格式或数据类型无效时
        HTTPException 404: 项目不存在时
        HTTPException 413: 文件大小超过限制时
        HTTPException 500: 服务器错误时
    """
    try:
        # 验证项目存在
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )

        # 验证文件大小
        file_size = 0
        content = await file.read()
        file_size = len(content)
        validate_file_size(file_size)

        # 验证文件格式
        try:
            file_format = get_file_format(file.filename)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # 验证数据类型
        try:
            validate_data_type(data_type)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # 重置文件指针
        await file.seek(0)

        # 保存文件
        file_path = await save_uploaded_file(project_id, file, file_size)

        # 创建数据库记录
        db_file = TestDataFileModel(
            project_id=project_id,
            file_name=file.filename,
            file_path=file_path,
            file_size=file_size,
            format=file_format,
            data_type=data_type
        )
        db.add(db_file)
        db.commit()
        db.refresh(db_file)

        logger.info(
            f"Uploaded test data: id={db_file.id}, project_id={project_id}, "
            f"filename={file.filename}, size={file_size}, format={file_format}"
        )

        return db_file

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading test data: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload test data"
        )


@router.get("/projects/{project_id}/test-data", response_model=List[TestDataFile])
def get_test_data_list(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    data_type: str = None,
    db: Session = Depends(get_db)
) -> List[TestDataFile]:
    """
    获取项目的测试数据列表

    Args:
        project_id: 项目ID
        skip: 跳过记录数，用于分页
        limit: 返回记录数限制
        data_type: 数据类型过滤（可选）
        db: 数据库会话

    Returns:
        测试数据文件列表

    Raises:
        HTTPException 404: 项目不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        # 验证项目存在
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )

        # 查询测试数据
        query = db.query(TestDataFileModel).filter(
            TestDataFileModel.project_id == project_id
        )

        # 按数据类型过滤
        if data_type:
            query = query.filter(TestDataFileModel.data_type == data_type)

        test_data_list = query.order_by(
            TestDataFileModel.uploaded_at.desc()
        ).offset(skip).limit(limit).all()

        logger.info(f"Retrieved {len(test_data_list)} test data files for project {project_id}")
        return test_data_list

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving test data list: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test data list"
        )


@router.get("/test-data/{test_data_id}", response_model=TestDataFile)
def get_test_data(
    test_data_id: int,
    db: Session = Depends(get_db)
) -> TestDataFile:
    """
    获取测试数据详情

    Args:
        test_data_id: 测试数据文件ID
        db: 数据库会话

    Returns:
        测试数据文件详情

    Raises:
        HTTPException 404: 测试数据不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        test_data = db.query(TestDataFileModel).filter(
            TestDataFileModel.id == test_data_id
        ).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found"
            )

        logger.info(f"Retrieved test data: id={test_data_id}")
        return test_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving test data {test_data_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve test data"
        )


@router.delete("/test-data/{test_data_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_test_data(
    test_data_id: int,
    db: Session = Depends(get_db)
) -> None:
    """
    删除测试数据文件

    Args:
        test_data_id: 测试数据文件ID
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException 404: 测试数据不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        # 获取测试数据记录
        test_data = db.query(TestDataFileModel).filter(
            TestDataFileModel.id == test_data_id
        ).first()

        if not test_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Test data file with id {test_data_id} not found"
            )

        # 删除物理文件
        file_path = Path(test_data.file_path)
        if file_path.exists():
            try:
                os.remove(file_path)
                logger.info(f"Deleted physical file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete physical file {file_path}: {str(e)}")

        # 删除数据库记录
        db.delete(test_data)
        db.commit()

        logger.info(f"Deleted test data: id={test_data_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting test data {test_data_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete test data"
        )
