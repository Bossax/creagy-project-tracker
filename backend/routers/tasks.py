"""API routes for task resources."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_session

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/", response_model=list[schemas.Task])
def list_tasks(
    project_id: Optional[int] = Query(default=None, description="Filter tasks by project"),
    db: Session = Depends(get_session),
) -> list[schemas.Task]:
    """Return all tasks, optionally filtered by project."""

    tasks = crud.get_tasks(db, project_id=project_id)
    return list(tasks)


@router.post("/", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task(task_in: schemas.TaskCreate, db: Session = Depends(get_session)) -> schemas.Task:
    """Create a new task."""

    task = crud.create_task(db, task_in)
    return task


@router.get("/{task_id}", response_model=schemas.Task)
def get_task(task_id: int, db: Session = Depends(get_session)) -> schemas.Task:
    """Retrieve a single task by its identifier."""

    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=schemas.Task)
def update_task(
    task_id: int,
    task_in: schemas.TaskUpdate,
    db: Session = Depends(get_session),
) -> schemas.Task:
    """Update an existing task."""

    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    updated_task = crud.update_task(db, task, task_in)
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_session)) -> None:
    """Delete a task by its identifier."""

    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    crud.delete_task(db, task)
