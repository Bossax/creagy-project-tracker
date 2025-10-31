"""Pydantic schemas for the Creagy project tracker API."""
from __future__ import annotations

from datetime import date, datetime
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
    budget_allocated: Optional[float] = Field(None, ge=0)
    budget_spent: Optional[float] = Field(None, ge=0)


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


class ProjectBudget(BaseModel):
    """Summary of project budget utilisation."""

    allocated: float = Field(0.0, ge=0)
    spent: float = Field(0.0, ge=0)
    remaining: float = Field(0.0)


class ProjectReportTask(BaseModel):
    """Minimal task details surfaced in weekly reports."""

    id: Optional[int] = None
    name: str
    owner: Optional[str] = None
    status: Optional[str] = None
    due_date: Optional[date] = None


class ProjectWeeklyReport(BaseModel):
    """Structured payload returned when generating weekly reports."""

    project_id: int
    project_name: str
    generated_at: datetime
    status_breakdown: dict[str, int]
    completion_percentage: float = Field(ge=0, le=100)
    budget: ProjectBudget
    upcoming_tasks: list[ProjectReportTask] = Field(default_factory=list)
    notes: Optional[str] = None


class PortfolioBudgetSummary(BaseModel):
    """Aggregate budget information across the project portfolio."""

    allocated: float = Field(0.0, ge=0)
    spent: float = Field(0.0, ge=0)
    remaining: float = Field(0.0)
    utilisation: float = Field(0.0, ge=0, le=100)


class ProjectHealthBreakdown(BaseModel):
    """Number of projects in a given health/status category."""

    status: str
    projects: int = Field(0, ge=0)


class TaskStatusBreakdown(BaseModel):
    """Distribution of tasks by workflow status."""

    status: str
    tasks: int = Field(0, ge=0)


class ProjectProgressSummary(BaseModel):
    """Completion details for a single project within the portfolio."""

    project_id: int
    project_name: str
    status: str
    completion_percentage: float = Field(0.0, ge=0, le=100)
    total_tasks: int = Field(0, ge=0)
    completed_tasks: int = Field(0, ge=0)


class ManDayAllocation(BaseModel):
    """Total man-day allocation captured across project tasks."""

    project_id: int
    project_name: str
    man_days: float = Field(0.0, ge=0)


class PortfolioReport(BaseModel):
    """Leadership-level overview of the entire delivery portfolio."""

    project_count: int = Field(0, ge=0)
    active_projects: int = Field(0, ge=0)
    total_tasks: int = Field(0, ge=0)
    budget: PortfolioBudgetSummary = Field(default_factory=PortfolioBudgetSummary)
    project_health: list[ProjectHealthBreakdown] = Field(default_factory=list)
    task_status: list[TaskStatusBreakdown] = Field(default_factory=list)
    project_progress: list[ProjectProgressSummary] = Field(default_factory=list)
    man_day_allocation: list[ManDayAllocation] = Field(default_factory=list)


__all__ = [
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "Project",
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "Task",
    "ProjectBudget",
    "ProjectReportTask",
    "ProjectWeeklyReport",
    "PortfolioBudgetSummary",
    "ProjectHealthBreakdown",
    "TaskStatusBreakdown",
    "ProjectProgressSummary",
    "ManDayAllocation",
    "PortfolioReport",
]
