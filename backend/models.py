import enum
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class ProjectStatus(str, enum.Enum):
    PLANNED = "planned"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"


class TaskStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    AT_RISK = "at_risk"
    BLOCKED = "blocked"
    COMPLETE = "complete"


class Project(Base):
    """Project entity with planning metadata."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    client: Mapped[str] = mapped_column(String(255), nullable=False)
    project_manager: Mapped[str] = mapped_column(String(255), nullable=False)
    budget: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status"),
        default=ProjectStatus.PLANNED,
    )

    tasks: Mapped[list["Task"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class Task(Base):
    """Task entity with workload and progress tracking."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    assignee: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    man_days: Mapped[float] = mapped_column(Float, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"),
        default=TaskStatus.NOT_STARTED,
    )
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship(back_populates="tasks")
