from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=list[schemas.TaskRead])
def read_tasks(
    assignee: str | None = Query(None),
    project_id: int | None = Query(None),
    status_filter: models.TaskStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
) -> list[schemas.TaskRead]:
    tasks = crud.list_tasks(db, assignee=assignee, project_id=project_id)
    if status_filter:
        tasks = [task for task in tasks if task.status == status_filter]
    return list(tasks)


@router.get("/{task_id}", response_model=schemas.TaskRead)
def read_task(task_id: int, db: Session = Depends(get_db)) -> schemas.TaskRead:
    try:
        task = crud.get_task(db, task_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return task


@router.post("/", response_model=schemas.TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(payload: schemas.TaskCreate, db: Session = Depends(get_db)) -> schemas.TaskRead:
    try:
        crud.ensure_projects_exist(db, [payload.project_id])
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return crud.create_task(db, payload)


@router.patch("/{task_id}", response_model=schemas.TaskRead)
def update_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db)) -> schemas.TaskRead:
    try:
        task = crud.get_task(db, task_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return crud.update_task(db, task, payload)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_task(task_id: int, db: Session = Depends(get_db)) -> None:
    try:
        task = crud.get_task(db, task_id)
    except NoResultFound as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    crud.delete_task(db, task)


@router.get("/assignees/list", response_model=list[str])
def list_assignees(db: Session = Depends(get_db)) -> list[str]:
    assignees = {task.assignee for task in crud.list_tasks(db)}
    return sorted(assignees)
