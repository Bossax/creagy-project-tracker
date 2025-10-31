"""API routes for project resources."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_session

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[schemas.Project])
def list_projects(db: Session = Depends(get_session)) -> list[schemas.Project]:
    """Return all projects."""

    projects = crud.get_projects(db)
    return list(projects)


@router.post("/", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(project_in: schemas.ProjectCreate, db: Session = Depends(get_session)) -> schemas.Project:
    """Create a new project."""

    project = crud.create_project(db, project_in)
    return project


@router.get("/{project_id}", response_model=schemas.Project)
def get_project(project_id: int, db: Session = Depends(get_session)) -> schemas.Project:
    """Retrieve a single project by its identifier."""

    project = crud.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=schemas.Project)
def update_project(
    project_id: int,
    project_in: schemas.ProjectUpdate,
    db: Session = Depends(get_session),
) -> schemas.Project:
    """Update an existing project."""

    project = crud.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    updated_project = crud.update_project(db, project, project_in)
    return updated_project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_session)) -> None:
    """Delete a project by its identifier."""

    project = crud.get_project(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    crud.delete_project(db, project)
