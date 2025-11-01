from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=list[schemas.ProjectRead])
def read_projects(
    status_filter: models.ProjectStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
) -> list[schemas.ProjectRead]:
    projects = crud.list_projects(db)
    if status_filter:
        projects = [project for project in projects if project.status == status_filter]
    return list(projects)


@router.get("/{project_id}", response_model=schemas.ProjectRead)
def read_project(project_id: int, db: Session = Depends(get_db)) -> schemas.ProjectRead:
    try:
        project = crud.get_project(db, project_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return project


@router.post("/", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: schemas.ProjectCreate, db: Session = Depends(get_db)) -> schemas.ProjectRead:
    return crud.create_project(db, payload)


@router.put("/{project_id}", response_model=schemas.ProjectRead)
def update_project(
    project_id: int,
    payload: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
) -> schemas.ProjectRead:
    try:
        project = crud.get_project(db, project_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return crud.update_project(db, project, payload)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_project(project_id: int, db: Session = Depends(get_db)) -> None:
    try:
        project = crud.get_project(db, project_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    crud.delete_project(db, project)


@router.get("/{project_id}/summary")
def project_summary(project_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        project = crud.get_project(db, project_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    total_tasks = len(project.tasks)
    completed = sum(1 for task in project.tasks if task.status == models.TaskStatus.COMPLETE)
    in_progress = sum(1 for task in project.tasks if task.status == models.TaskStatus.IN_PROGRESS)
    total_man_days = sum(task.man_days for task in project.tasks)
    average_progress = (
        sum(task.progress for task in project.tasks) / total_tasks if total_tasks else 0.0
    )

    return {
        "project_id": project.id,
        "name": project.name,
        "status": project.status,
        "total_tasks": total_tasks,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "total_man_days": total_man_days,
        "average_progress": round(average_progress, 4),
    }
