from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import CustomSignal, MessageResponse

router = APIRouter()


@router.get("/projects/{project_id}/custom-signals")
def get_custom_signals(project_id: int, db: Session = Depends(get_db)):
    """获取自定义信号列表"""
    # TODO: 实现查询逻辑
    return []


@router.post("/projects/{project_id}/custom-signals", response_model=CustomSignal)
def create_custom_signal(project_id: int, signal: dict, db: Session = Depends(get_db)):
    """创建自定义信号"""
    # TODO: 实现创建逻辑
    return MessageResponse(message="Custom signal creation not implemented yet")


@router.put("/custom-signals/{signal_id}")
def update_custom_signal(signal_id: int, signal: dict, db: Session = Depends(get_db)):
    """更新自定义信号"""
    # TODO: 实现更新逻辑
    return MessageResponse(message="Custom signal update not implemented yet")


@router.delete("/custom-signals/{signal_id}")
def delete_custom_signal(signal_id: int, db: Session = Depends(get_db)):
    """删除自定义信号"""
    # TODO: 实现删除逻辑
    return MessageResponse(message="Custom signal deleted")
