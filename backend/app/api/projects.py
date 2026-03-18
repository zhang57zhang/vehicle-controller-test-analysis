"""
项目管理API路由

提供项目的CRUD操作，包括创建、读取、更新和删除项目。
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.database import get_db
from app.schemas import Project, ProjectCreate, ProjectUpdate
from app.models import Project as ProjectModel

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=List[Project], status_code=status.HTTP_200_OK)
def get_projects(
    skip: int = 0,
    limit: int = 100,
    name: str = None,
    db: Session = Depends(get_db)
) -> List[Project]:
    """
    获取项目列表

    Args:
        skip: 跳过记录数，用于分页
        limit: 返回记录数限制，最大100
        name: 项目名称过滤（可选）
        db: 数据库会话

    Returns:
        项目列表

    Raises:
        HTTPException: 当查询出错时返回500错误
    """
    try:
        query = db.query(ProjectModel)

        # 按名称过滤
        if name:
            query = query.filter(ProjectModel.name.contains(name))

        projects = query.order_by(ProjectModel.created_at.desc()).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(projects)} projects (skip={skip}, limit={limit})")
        return projects

    except Exception as e:
        logger.error(f"Error retrieving projects: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve projects"
        )


@router.get("/{project_id}", response_model=Project, status_code=status.HTTP_200_OK)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    """
    获取项目详情

    Args:
        project_id: 项目ID
        db: 数据库会话

    Returns:
        项目详情

    Raises:
        HTTPException 404: 当项目不存在时
    """
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            logger.warning(f"Project not found: id={project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )
        logger.info(f"Retrieved project: id={project_id}, name={project.name}")
        return project

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project"
        )


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    """
    创建新项目

    Args:
        project: 项目创建数据
        db: 数据库会话

    Returns:
        创建的项目

    Raises:
        HTTPException 400: 当数据验证失败时
        HTTPException 500: 当数据库操作失败时
    """
    try:
        # 验证项目名称唯一性
        existing = db.query(ProjectModel).filter(ProjectModel.name == project.name).first()
        if existing:
            logger.warning(f"Project name already exists: {project.name}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with name '{project.name}' already exists"
            )

        # 创建项目
        db_project = ProjectModel(**project.model_dump())
        db.add(db_project)
        db.commit()
        db.refresh(db_project)

        logger.info(f"Created project: id={db_project.id}, name={db_project.name}")
        return db_project

    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Validation error creating project: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project data: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating project: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.put("/{project_id}", response_model=Project, status_code=status.HTTP_200_OK)
def update_project(
    project_id: int,
    project: ProjectUpdate,
    db: Session = Depends(get_db)
) -> Project:
    """
    更新项目信息

    Args:
        project_id: 项目ID
        project: 项目更新数据
        db: 数据库会话

    Returns:
        更新后的项目

    Raises:
        HTTPException 404: 当项目不存在时
        HTTPException 400: 当数据验证失败时
        HTTPException 500: 当数据库操作失败时
    """
    try:
        db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not db_project:
            logger.warning(f"Project not found for update: id={project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )

        # 检查名称唯一性（如果更新了名称）
        if project.name and project.name != db_project.name:
            existing = db.query(ProjectModel).filter(
                ProjectModel.name == project.name,
                ProjectModel.id != project_id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Project with name '{project.name}' already exists"
                )

        # 更新字段
        update_data = project.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_project, key, value)

        db.commit()
        db.refresh(db_project)

        logger.info(f"Updated project: id={project_id}, fields={list(update_data.keys())}")
        return db_project

    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Validation error updating project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project data: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    """
    删除项目

    Args:
        project_id: 项目ID
        db: 数据库会话

    Returns:
        None

    Raises:
        HTTPException 404: 当项目不存在时
        HTTPException 409: 当项目有关联数据时
        HTTPException 500: 当数据库操作失败时
    """
    try:
        db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not db_project:
            logger.warning(f"Project not found for deletion: id={project_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found"
            )

        # 检查是否有关联数据
        if db_project.test_data_files:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete project with associated test data files"
            )
        if db_project.dbc_files:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete project with associated DBC files"
            )

        db.delete(db_project)
        db.commit()

        logger.info(f"Deleted project: id={project_id}, name={db_project.name}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting project {project_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )
