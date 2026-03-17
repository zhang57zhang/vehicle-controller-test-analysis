from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import DBCFile, MessageResponse

router = APIRouter()


@router.post("/projects/{project_id}/dbc/upload", response_model=DBCFile)
async def upload_dbc(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """上传DBC文件"""
    # TODO: 实现DBC文件上传和解析
    return MessageResponse(message="DBC upload not implemented yet")


@router.get("/projects/{project_id}/dbc")
def get_dbc_list(project_id: int, db: Session = Depends(get_db)):
    """获取项目的DBC文件列表"""
    # TODO: 实现查询逻辑
    return []


@router.post("/dbc/{dbc_id}/parse")
def parse_dbc(dbc_id: int, db: Session = Depends(get_db)):
    """解析DBC文件"""
    # TODO: 实现DBC解析逻辑
    return MessageResponse(message="DBC parsing not implemented yet")
