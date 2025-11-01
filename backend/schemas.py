from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, condecimal, field_validator

from .models import ProjectStatus, TaskStatus


class ProjectBase(BaseModel):
    name: str = Field(..., max_length=255)
    client: str = Field(..., max_length=255)
    project_manager: str = Field(..., max_length=255)
    budget: condecimal(max_digits=12, decimal_places=2)
    start_date: date
    end_date: Optional[date] = None
    status: ProjectStatus = ProjectStatus.PLANNED


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    client: Optional[str] = Field(None, max_length=255)
    project_manager: Optional[str] = Field(None, max_length=255)
    budget: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None


class TaskBase(BaseModel):
    project_id: int
    name: str = Field(..., max_length=255)
    assignee: str = Field(..., max_length=255)
    man_days: float = Field(..., ge=0)
    start_date: date
    end_date: Optional[date] = None
    status: TaskStatus = TaskStatus.NOT_STARTED
    progress: float = Field(0.0, ge=0.0, le=1.0)
    remarks: Optional[str] = None

    @field_validator("progress")
    @classmethod
    def clamp_progress(cls, value: float) -> float:
        return max(0.0, min(1.0, value))


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    assignee: Optional[str] = Field(None, max_length=255)
    man_days: Optional[float] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    remarks: Optional[str] = None

    @field_validator("progress")
    @classmethod
    def clamp_progress(cls, value: float | None) -> float | None:
        if value is None:
            return value
        return max(0.0, min(1.0, value))


class TaskRead(BaseModel):
    id: int
    project_id: int
    name: str
    assignee: str
    man_days: float
    start_date: date
    end_date: Optional[date]
    status: TaskStatus
    progress: float
    remarks: Optional[str]

    model_config = {"from_attributes": True}


class ProjectRead(BaseModel):
    id: int
    name: str
    client: str
    project_manager: str
    budget: Decimal
    start_date: date
    end_date: Optional[date]
    status: ProjectStatus
    tasks: list[TaskRead] = []

    model_config = {"from_attributes": True}


class PortfolioSummary(BaseModel):
    total_projects: int
    active_projects: int
    completed_projects: int
    total_man_days: float
    overall_completion_rate: float
    budget_utilization: float


class UtilizationBreakdown(BaseModel):
    assignee: str
    man_days: float
    tasks: int
    in_progress: int
    completed: int
