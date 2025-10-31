"""Pydantic schemas for the Creagy project tracker API."""
from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """Shared attributes for project operations."""

    name: Optional[str] = Field(None, max_length=255)
    owner: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""

    name: str = Field(..., max_length=255)


class ProjectUpdate(ProjectBase):
    """Schema for updating an existing project."""

    pass


class TaskBase(BaseModel):
    """Shared attributes for task operations."""

    name: Optional[str] = Field(None, max_length=255)
    owner: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = Field(None, max_length=50)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class TaskCreate(TaskBase):
    """Schema for creating a new task."""

    name: str = Field(..., max_length=255)
    project_id: int


class TaskUpdate(TaskBase):
    """Schema for updating an existing task."""

    project_id: Optional[int] = None


class Task(TaskBase):
    """Schema for reading task information from the database."""

    id: int
    project_id: int
    name: str = Field(..., max_length=255)

    model_config = ConfigDict(from_attributes=True)


class Project(ProjectBase):
    """Schema for reading project information along with its tasks."""

    id: int
    name: str = Field(..., max_length=255)
    tasks: list[Task] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


__all__ = [
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "Project",
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "Task",
]
