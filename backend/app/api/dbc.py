"""
DBC文件API路由

提供DBC文件的上传、查询和解析功能。
"""

import os
import logging
import aiofiles
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.config import settings
from app.schemas import DBCFile, MessageResponse
from app.models import Project as ProjectModel, DBCFile as DBCFileModel
from app.services.dbc_parser import DBCParser, ParseError, FileFormatError

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


class DBCParseRequest(BaseModel):
    """DBC解析请求"""

    parse_type: str = "summary"  # summary, messages, signals


class DBCParseResponse(BaseModel):
    """DBC解析响应"""

    file_name: str
    message_count: int
    signal_count: int
    messages: Optional[List[Dict[str, Any]]] = None


async def save_dbc_file(project_id: int, file: UploadFile) -> str:
    """
    保存DBC文件

    Args:
        project_id: 项目ID
        file: 上传的文件对象

    Returns:
        保存的文件路径

    Raises:
        HTTPException: 当文件保存失败时
    """
    try:
        # 创建项目目录
        project_dir = Path(settings.UPLOAD_DIR) / f"project_{project_id}" / "dbc"
        project_dir.mkdir(parents=True, exist_ok=True)

        # 验证文件扩展名
        ext = Path(file.filename).suffix.lower()
        if ext not in {".dbc", ".arxml", ".xml"}:
            raise ValueError(f"Invalid DBC file extension: {ext}. Supported: .dbc, .arxml, .xml")

        # 生成唯一文件名
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = project_dir / safe_filename

        # 保存文件
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        logger.info(f"Saved DBC file: {file_path}")
        return str(file_path)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error saving DBC file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save DBC file: {str(e)}",
        )


@router.post(
    "/projects/{project_id}/dbc/upload", response_model=DBCFile, status_code=status.HTTP_201_CREATED
)
async def upload_dbc(
    project_id: int,
    file: UploadFile = File(...),
    version: str = None,
    db: Session = Depends(get_db),
) -> DBCFile:
    """
    上传DBC文件

    Args:
        project_id: 项目ID
        file: 上传的DBC文件
        version: DBC版本号（可选）
        db: 数据库会话

    Returns:
        创建的DBC文件记录

    Raises:
        HTTPException 400: 文件格式无效时
        HTTPException 404: 项目不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        # 验证项目存在
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        # 保存文件
        file_path = await save_dbc_file(project_id, file)

        # 验证DBC文件格式
        try:
            parser = DBCParser(file_path)
            parser.load()
            logger.info(f"DBC file validated successfully: {file.filename}")
        except FileFormatError as e:
            # 删除无效文件
            if Path(file_path).exists():
                os.remove(file_path)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except ParseError as e:
            # 删除无效文件
            if Path(file_path).exists():
                os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse DBC file: {str(e)}",
            )

        # 创建数据库记录
        db_dbc = DBCFileModel(
            project_id=project_id, file_name=file.filename, file_path=file_path, version=version
        )
        db.add(db_dbc)
        db.commit()
        db.refresh(db_dbc)

        logger.info(
            f"Uploaded DBC file: id={db_dbc.id}, project_id={project_id}, filename={file.filename}"
        )

        return db_dbc

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading DBC file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload DBC file"
        )


@router.get("/projects/{project_id}/dbc", response_model=List[DBCFile])
def get_dbc_list(
    project_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
) -> List[DBCFile]:
    """
    获取项目的DBC文件列表

    Args:
        project_id: 项目ID
        skip: 跳过记录数，用于分页
        limit: 返回记录数限制
        db: 数据库会话

    Returns:
        DBC文件列表

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
                detail=f"Project with id {project_id} not found",
            )

        # 查询DBC文件
        dbc_files = (
            db.query(DBCFileModel)
            .filter(DBCFileModel.project_id == project_id)
            .order_by(DBCFileModel.uploaded_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        logger.info(f"Retrieved {len(dbc_files)} DBC files for project {project_id}")
        return dbc_files

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving DBC list: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve DBC list"
        )


@router.get("/dbc/{dbc_id}", response_model=DBCFile)
def get_dbc(dbc_id: int, db: Session = Depends(get_db)) -> DBCFile:
    """
    获取DBC文件详情

    Args:
        dbc_id: DBC文件ID
        db: 数据库会话

    Returns:
        DBC文件详情

    Raises:
        HTTPException 404: DBC文件不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        dbc_file = db.query(DBCFileModel).filter(DBCFileModel.id == dbc_id).first()

        if not dbc_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"DBC file with id {dbc_id} not found"
            )

        logger.info(f"Retrieved DBC file: id={dbc_id}")
        return dbc_file

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving DBC file {dbc_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve DBC file"
        )


@router.post("/dbc/{dbc_id}/parse", response_model=DBCParseResponse)
def parse_dbc(
    dbc_id: int, request: DBCParseRequest = DBCParseRequest(), db: Session = Depends(get_db)
) -> DBCParseResponse:
    """
    解析DBC文件

    Args:
        dbc_id: DBC文件ID
        request: 解析请求参数
        db: 数据库会话

    Returns:
        解析结果

    Raises:
        HTTPException 404: DBC文件不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        # 获取DBC文件记录
        dbc_file = db.query(DBCFileModel).filter(DBCFileModel.id == dbc_id).first()

        if not dbc_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"DBC file with id {dbc_id} not found"
            )

        # 验证文件存在
        file_path = Path(dbc_file.file_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="DBC file not found on disk"
            )

        # 解析DBC文件
        parser = DBCParser(str(file_path))
        parser.load()

        # 根据请求类型返回不同数据
        if request.parse_type == "summary":
            summary = parser.get_summary()
            return DBCParseResponse(**summary)

        elif request.parse_type == "messages":
            messages = parser.get_messages()
            summary = parser.get_summary()
            return DBCParseResponse(
                file_name=summary["file_name"],
                message_count=summary["message_count"],
                signal_count=summary["signal_count"],
                messages=messages,
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid parse_type: {request.parse_type}. Supported: summary, messages",
            )

    except HTTPException:
        raise
    except FileFormatError as e:
        logger.error(f"DBC format error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ParseError as e:
        logger.error(f"DBC parse error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error parsing DBC file: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to parse DBC file"
        )


@router.get("/dbc/{dbc_id}/messages")
def get_dbc_messages(dbc_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    获取DBC文件的所有消息定义

    Args:
        dbc_id: DBC文件ID
        db: 数据库会话

    Returns:
        消息定义列表

    Raises:
        HTTPException 404: DBC文件不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        # 获取DBC文件记录
        dbc_file = db.query(DBCFileModel).filter(DBCFileModel.id == dbc_id).first()

        if not dbc_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"DBC file with id {dbc_id} not found"
            )

        # 解析DBC文件
        parser = DBCParser(dbc_file.file_path)
        parser.load()

        messages = parser.get_messages()
        logger.info(f"Retrieved {len(messages)} messages from DBC {dbc_id}")

        return {"messages": messages}

    except HTTPException:
        raise
    except FileFormatError as e:
        logger.error(f"DBC format error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ParseError as e:
        logger.error(f"DBC parse error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting DBC messages: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get DBC messages"
        )


@router.get("/dbc/{dbc_id}/signals")
def get_dbc_signals(dbc_id: int, db: Session = Depends(get_db)) -> Dict[str, List[str]]:
    """
    获取DBC文件的所有信号名称

    Args:
        dbc_id: DBC文件ID
        db: 数据库会话

    Returns:
        信号名称列表

    Raises:
        HTTPException 404: DBC文件不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        # 获取DBC文件记录
        dbc_file = db.query(DBCFileModel).filter(DBCFileModel.id == dbc_id).first()

        if not dbc_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"DBC file with id {dbc_id} not found"
            )

        # 解析DBC文件
        parser = DBCParser(dbc_file.file_path)
        parser.load()

        signals = parser.get_all_signal_names()
        logger.info(f"Retrieved {len(signals)} signals from DBC {dbc_id}")

        return {"signals": signals}

    except HTTPException:
        raise
    except FileFormatError as e:
        logger.error(f"DBC format error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ParseError as e:
        logger.error(f"DBC parse error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting DBC signals: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get DBC signals"
        )


@router.get("/projects/{project_id}/dbc-signals")
def get_project_dbc_signals(project_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    获取项目的DBC信号列表（按Message分组）

    Args:
        project_id: 项目ID
        db: 数据库会话

    Returns:
        DBC信号列表，按Message分组

    Raises:
        HTTPException 404: 项目不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )

        dbc_files = db.query(DBCFileModel).filter(DBCFileModel.project_id == project_id).all()

        if not dbc_files:
            return {"messages": [], "signals": [], "signal_count": 0}

        all_messages = []
        all_signals = []

        for dbc_file in dbc_files:
            file_path = Path(dbc_file.file_path)
            if not file_path.exists():
                continue

            try:
                parser = DBCParser(str(file_path))
                parser.load()
                messages = parser.get_messages()

                for msg in messages:
                    msg_info = {
                        "dbc_file_id": dbc_file.id,
                        "dbc_file_name": dbc_file.file_name,
                        "frame_id": msg["frame_id"],
                        "name": msg["name"],
                        "length": msg["length"],
                        "cycle_time": msg.get("cycle_time"),
                        "signals": [],
                    }

                    for sig in msg["signals"]:
                        signal_info = {
                            "name": sig["name"],
                            "full_name": f"{msg['name']}.{sig['name']}",
                            "unit": sig.get("unit"),
                            "minimum": sig.get("minimum"),
                            "maximum": sig.get("maximum"),
                            "scale": sig.get("scale", 1),
                            "offset": sig.get("offset", 0),
                            "comment": sig.get("comment"),
                            "message_name": msg["name"],
                            "dbc_file_id": dbc_file.id,
                        }
                        msg_info["signals"].append(signal_info)
                        all_signals.append(signal_info)

                    all_messages.append(msg_info)

            except (FileFormatError, ParseError) as e:
                logger.warning(f"Failed to parse DBC file {dbc_file.file_name}: {str(e)}")
                continue

        logger.info(
            f"Retrieved {len(all_signals)} DBC signals from {len(all_messages)} messages for project {project_id}"
        )

        return {
            "messages": all_messages,
            "signals": all_signals,
            "signal_count": len(all_signals),
            "message_count": len(all_messages),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project DBC signals: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get project DBC signals",
        )


@router.delete("/dbc/{dbc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dbc(dbc_id: int, db: Session = Depends(get_db)) -> None:
    """
    删除DBC文件

    Args:
        dbc_id: DBC文件ID
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException 404: DBC文件不存在时
        HTTPException 500: 服务器错误时
    """
    try:
        # 获取DBC文件记录
        dbc_file = db.query(DBCFileModel).filter(DBCFileModel.id == dbc_id).first()

        if not dbc_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"DBC file with id {dbc_id} not found"
            )

        # 删除物理文件
        file_path = Path(dbc_file.file_path)
        if file_path.exists():
            try:
                os.remove(file_path)
                logger.info(f"Deleted physical file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete physical file {file_path}: {str(e)}")

        # 删除数据库记录
        db.delete(dbc_file)
        db.commit()

        logger.info(f"Deleted DBC file: id={dbc_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting DBC file {dbc_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete DBC file"
        )
