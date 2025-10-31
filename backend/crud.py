"""Reusable CRUD helper functions for SQLAlchemy models."""
from __future__ import annotations

from typing import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models, schemas


def get_project(db: Session, project_id: int) -> models.Project | None:
    """Retrieve a project by its primary key."""

    return db.get(models.Project, project_id)


def get_projects(db: Session) -> Sequence[models.Project]:
    """Return all projects ordered by their identifier."""

    statement = select(models.Project).order_by(models.Project.id)
    return db.scalars(statement).all()


def create_project(db: Session, project_in: schemas.ProjectCreate) -> models.Project:
    """Persist a new project based on the provided schema."""

    project = models.Project(**project_in.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(
    db: Session,
    project: models.Project,
    project_in: schemas.ProjectUpdate,
) -> models.Project:
    """Apply updates to an existing project and persist the changes."""

    update_data = project_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project: models.Project) -> None:
    """Delete a project from the database."""

    db.delete(project)
    db.commit()


def get_task(db: Session, task_id: int) -> models.Task | None:
    """Retrieve a task by its primary key."""

    return db.get(models.Task, task_id)


def get_tasks(db: Session, *, project_id: int | None = None) -> Sequence[models.Task]:
    """Return tasks, optionally filtered by project."""

    statement = select(models.Task).order_by(models.Task.id)
    if project_id is not None:
        statement = statement.where(models.Task.project_id == project_id)

    return db.scalars(statement).all()


def create_task(db: Session, task_in: schemas.TaskCreate) -> models.Task:
    """Persist a new task based on the provided schema."""

    task = models.Task(**task_in.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(
    db: Session,
    task: models.Task,
    task_in: schemas.TaskUpdate,
) -> models.Task:
    """Apply updates to an existing task and persist the changes."""

    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: models.Task) -> None:
    """Delete a task from the database."""

    db.delete(task)
    db.commit()


__all__ = [
    "get_project",
    "get_projects",
    "create_project",
    "update_project",
    "delete_project",
    "get_task",
    "get_tasks",
    "create_task",
    "update_task",
    "delete_task",
]
