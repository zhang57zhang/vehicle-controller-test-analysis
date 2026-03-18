"""
通用文件上传API路由

提供文件上传功能，支持多种文件类型：CSV、Excel、MATLAB .mat、DBC、Vector CAN log。
"""
import os
import logging
import aiofiles
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.schemas import MessageResponse

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 支持的文件类型映射
FILE_TYPE_MAPPING = {
    '.csv': 'csv',
    '.xlsx': 'excel',
    '.xls': 'excel',
    '.mat': 'mat',
    '.dbc': 'dbc',
    '.arxml': 'dbc',
    '.log': 'log',
    '.blf': 'log',
    '.asc': 'log'
}

# 允许的MIME类型
ALLOWED_MIME_TYPES = {
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/octet-stream',
    'text/plain'
}


def validate_file_type(filename: str) -> str:
    """
    验证文件类型

    Args:
        filename: 文件名

    Returns:
        文件类型字符串

    Raises:
        ValueError: 当文件类型不支持时
    """
    ext = Path(filename).suffix.lower()
    if ext not in FILE_TYPE_MAPPING:
        raise ValueError(f"Unsupported file type: {ext}. Supported types: {', '.join(FILE_TYPE_MAPPING.keys())}")
    return FILE_TYPE_MAPPING[ext]


def validate_file_size(file_size: int) -> None:
    """
    验证文件大小

    Args:
        file_size: 文件大小（字节）

    Raises:
        ValueError: 当文件大小超过限制时
    """
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise ValueError(
            f"File size {file_size} bytes exceeds maximum allowed size {settings.MAX_UPLOAD_SIZE} bytes "
            f"({settings.MAX_UPLOAD_SIZE / (1024*1024):.1f} MB)"
        )


def generate_unique_filename(original_filename: str) -> str:
    """
    生成唯一文件名

    Args:
        original_filename: 原始文件名

    Returns:
        唯一文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    ext = Path(original_filename).suffix
    base_name = Path(original_filename).stem
    # 清理文件名中的特殊字符
    safe_base_name = "".join(c for c in base_name if c.isalnum() or c in ('_', '-', '.'))
    return f"{timestamp}_{safe_base_name}{ext}"


async def save_file(file: UploadFile, upload_dir: Path) -> str:
    """
    保存上传的文件

    Args:
        file: 上传的文件对象
        upload_dir: 上传目录

    Returns:
        保存的文件路径

    Raises:
        HTTPException: 当文件保存失败时
    """
    try:
        # 确保上传目录存在
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一文件名
        unique_filename = generate_unique_filename(file.filename)
        file_path = upload_dir / unique_filename

        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        logger.info(f"Saved file: {file_path} ({len(content)} bytes)")
        return str(file_path)

    except Exception as e:
        logger.error(f"Error saving file {file.filename}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


@router.post(
    "/api/files/upload",
    status_code=status.HTTP_201_CREATED
)
async def upload_file(
    file: UploadFile = File(...),
    description: Optional[str] = None
) -> dict:
    """
    通用文件上传

    支持的文件类型：CSV、Excel、MATLAB .mat、DBC、Vector CAN log
    文件大小限制：500MB

    Args:
        file: 上传的文件
        description: 文件描述（可选）

    Returns:
        包含文件ID和基本信息的字典

    Raises:
        HTTPException 400: 文件类型或大小验证失败时
        HTTPException 500: 服务器错误时
    """
    try:
        # 读取文件内容以获取大小
        content = await file.read()
        file_size = len(content)

        # 验证文件大小
        try:
            validate_file_size(file_size)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=str(e)
            )

        # 验证文件类型
        try:
            file_type = validate_file_type(file.filename)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

        # 重置文件指针
        await file.seek(0)

        # 保存文件
        upload_dir = Path(settings.UPLOAD_DIR)
        file_path = await save_file(file, upload_dir)

        # 生成简单的文件ID（使用文件路径的哈希值）
        import hashlib
        file_id = hashlib.md5(file_path.encode()).hexdigest()[:16]

        # 返回文件信息
        result = {
            "file_id": file_id,
            "file_name": file.filename,
            "file_type": file_type,
            "file_size": file_size,
            "file_path": file_path,
            "description": description,
            "uploaded_at": datetime.now().isoformat()
        }

        logger.info(
            f"Uploaded file: id={file_id}, name={file.filename}, "
            f"type={file_type}, size={file_size}"
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file"
        )


@router.get("/api/files/{file_id}", status_code=status.HTTP_200_OK)
async def get_file_info(file_id: str) -> dict:
    """
    获取文件信息

    Args:
        file_id: 文件ID

    Returns:
        文件信息字典

    Raises:
        HTTPException 404: 文件不存在时
    """
    try:
        # 查找文件（这里简化处理，实际应该从数据库查询）
        upload_dir = Path(settings.UPLOAD_DIR)
        files = list(upload_dir.glob(f"*{file_id}*"))

        if not files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with id {file_id} not found"
            )

        file_path = files[0]
        file_stat = os.stat(file_path)

        # 推断文件类型
        ext = file_path.suffix.lower()
        file_type = FILE_TYPE_MAPPING.get(ext, 'unknown')

        return {
            "file_id": file_id,
            "file_name": file_path.name,
            "file_type": file_type,
            "file_size": file_stat.st_size,
            "file_path": str(file_path),
            "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file info for {file_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get file info"
        )


@router.delete("/api/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: str) -> None:
    """
    删除文件

    Args:
        file_id: 文件ID

    Returns:
        None

    Raises:
        HTTPException 404: 文件不存在时
    """
    try:
        # 查找文件
        upload_dir = Path(settings.UPLOAD_DIR)
        files = list(upload_dir.glob(f"*{file_id}*"))

        if not files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File with id {file_id} not found"
            )

        file_path = files[0]

        # 删除文件
        os.remove(file_path)
        logger.info(f"Deleted file: {file_path}")

        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file"
        )
