from __future__ import annotations

from typing import Iterable, Sequence

from sqlalchemy import Select, case, func, select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from . import models, schemas


def _project_query() -> Select[tuple[models.Project]]:
    return select(models.Project).order_by(models.Project.start_date)


def _task_query() -> Select[tuple[models.Task]]:
    return select(models.Task).order_by(models.Task.start_date)


def list_projects(db: Session) -> Sequence[models.Project]:
    return db.scalars(_project_query()).all()


def get_project(db: Session, project_id: int) -> models.Project:
    project = db.get(models.Project, project_id)
    if not project:
        raise NoResultFound(f"Project {project_id} not found")
    return project


def create_project(db: Session, payload: schemas.ProjectCreate) -> models.Project:
    project = models.Project(**payload.model_dump())
    db.add(project)
    db.flush()
    db.refresh(project)
    return project


def update_project(
    db: Session,
    project: models.Project,
    payload: schemas.ProjectUpdate,
) -> models.Project:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(project, field, value)
    db.add(project)
    db.flush()
    db.refresh(project)
    return project


def delete_project(db: Session, project: models.Project) -> None:
    db.delete(project)
    db.flush()


def list_tasks(db: Session, *, assignee: str | None = None, project_id: int | None = None) -> Sequence[models.Task]:
    query = _task_query()
    if assignee:
        query = query.where(models.Task.assignee == assignee)
    if project_id:
        query = query.where(models.Task.project_id == project_id)
    return db.scalars(query).all()


def get_task(db: Session, task_id: int) -> models.Task:
    task = db.get(models.Task, task_id)
    if not task:
        raise NoResultFound(f"Task {task_id} not found")
    return task


def create_task(db: Session, payload: schemas.TaskCreate) -> models.Task:
    task = models.Task(**payload.model_dump())
    db.add(task)
    db.flush()
    db.refresh(task)
    return task


def update_task(db: Session, task: models.Task, payload: schemas.TaskUpdate) -> models.Task:
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(task, field, value)
    db.add(task)
    db.flush()
    db.refresh(task)
    return task


def delete_task(db: Session, task: models.Task) -> None:
    db.delete(task)
    db.flush()


def portfolio_summary(db: Session) -> schemas.PortfolioSummary:
    total_projects = db.scalar(select(func.count(models.Project.id))) or 0
    active_projects = db.scalar(
        select(func.count(models.Project.id)).where(models.Project.status == models.ProjectStatus.ACTIVE)
    ) or 0
    completed_projects = db.scalar(
        select(func.count(models.Project.id)).where(models.Project.status == models.ProjectStatus.COMPLETED)
    ) or 0
    total_man_days = db.scalar(select(func.coalesce(func.sum(models.Task.man_days), 0.0))) or 0.0
    total_tasks = db.scalar(select(func.count(models.Task.id))) or 0
    completed_tasks = db.scalar(
        select(func.count(models.Task.id)).where(models.Task.status == models.TaskStatus.COMPLETE)
    ) or 0
    overall_completion_rate = (completed_tasks / total_tasks) if total_tasks else 0.0

    total_budget = db.scalar(select(func.coalesce(func.sum(models.Project.budget), 0.0))) or 0.0
    budget_float = float(total_budget) if total_budget else 0.0
    budget_utilization = (total_man_days / budget_float) if budget_float else 0.0

    return schemas.PortfolioSummary(
        total_projects=total_projects,
        active_projects=active_projects,
        completed_projects=completed_projects,
        total_man_days=float(total_man_days),
        overall_completion_rate=float(round(overall_completion_rate, 4)),
        budget_utilization=float(round(budget_utilization, 4)),
    )


def team_utilization(db: Session) -> list[schemas.UtilizationBreakdown]:
    rows = db.execute(
        select(
            models.Task.assignee,
            func.coalesce(func.sum(models.Task.man_days), 0.0),
            func.count(models.Task.id),
            func.coalesce(func.sum(case((models.Task.status == models.TaskStatus.IN_PROGRESS, 1), else_=0)), 0),
            func.coalesce(func.sum(case((models.Task.status == models.TaskStatus.COMPLETE, 1), else_=0)), 0),
        )
        .group_by(models.Task.assignee)
        .order_by(models.Task.assignee)
    ).all()

    breakdown: list[schemas.UtilizationBreakdown] = []
    for assignee, man_days, total_tasks, in_progress, completed in rows:
        breakdown.append(
            schemas.UtilizationBreakdown(
                assignee=assignee,
                man_days=float(man_days or 0.0),
                tasks=int(total_tasks or 0),
                in_progress=int(in_progress or 0),
                completed=int(completed or 0),
            )
        )
    return breakdown


def ensure_projects_exist(db: Session, project_ids: Iterable[int]) -> None:
    missing: list[int] = []
    for project_id in project_ids:
        if not db.get(models.Project, project_id):
            missing.append(project_id)
    if missing:
        raise NoResultFound(f"Projects not found: {missing}")
