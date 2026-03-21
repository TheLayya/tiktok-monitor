import logging
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.monitor import Project, MonitorAccount
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


def get_projects(db: Session) -> List[Project]:
    """获取所有项目，附带 account_count。"""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    # 批量统计每个项目的账号数
    counts = (
        db.query(MonitorAccount.project_id, func.count(MonitorAccount.id).label("cnt"))
        .group_by(MonitorAccount.project_id)
        .all()
    )
    count_map = {row.project_id: row.cnt for row in counts}
    for project in projects:
        project.account_count = count_map.get(project.id, 0)
    return projects


def get_project(db: Session, project_id: int) -> Optional[Project]:
    """获取单个项目（附带 account_count）。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.account_count = (
            db.query(func.count(MonitorAccount.id))
            .filter(MonitorAccount.project_id == project_id)
            .scalar()
        )
    return project


def create_project(db: Session, data: ProjectCreate) -> Project:
    """创建项目，名称唯一校验。"""
    existing = db.query(Project).filter(Project.name == data.name).first()
    if existing:
        raise ValueError(f"Project name '{data.name}' already exists")

    project = Project(
        name=data.name,
        description=data.description,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    project.account_count = 0
    return project


def update_project(
    db: Session, project_id: int, data: ProjectUpdate
) -> Optional[Project]:
    """更新项目字段。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    update_data = data.model_dump(exclude_unset=True)

    # 名称唯一校验（排除自身）
    if "name" in update_data and update_data["name"] != project.name:
        conflict = (
            db.query(Project)
            .filter(Project.name == update_data["name"], Project.id != project_id)
            .first()
        )
        if conflict:
            raise ValueError(f"Project name '{update_data['name']}' already exists")

    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    project.account_count = (
        db.query(func.count(MonitorAccount.id))
        .filter(MonitorAccount.project_id == project_id)
        .scalar()
    )
    return project


def delete_project(db: Session, project_id: int) -> None:
    """删除项目。若项目下仍有账号则拒绝删除，抛出 ValueError。"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise LookupError(f"Project {project_id} not found")

    account_count = (
        db.query(func.count(MonitorAccount.id))
        .filter(MonitorAccount.project_id == project_id)
        .scalar()
    )
    if account_count > 0:
        raise ValueError(
            f"Cannot delete project with {account_count} account(s). "
            "Please remove or move all accounts first."
        )

    db.delete(project)
    db.commit()
