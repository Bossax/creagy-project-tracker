from __future__ import annotations

from datetime import date
from typing import List

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    employees: Mapped[List["Employee"]] = relationship("Employee", back_populates="team")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Team(id={self.id!r}, name={self.name!r})"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), nullable=True)

    team: Mapped[Team | None] = relationship("Team", back_populates="employees")
    managed_projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="project_manager", foreign_keys="Project.project_manager_id"
    )
    created_projects: Mapped[List["Project"]] = relationship(
        "Project", back_populates="created_by", foreign_keys="Project.created_by_id"
    )
    assigned_tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="assignee", foreign_keys="Task.assignee_id"
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Employee(id={self.id!r}, name={self.name!r})"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    projects: Mapped[List["Project"]] = relationship("Project", back_populates="client")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    project_manager_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)
    budget: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Active")
    created_by_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)

    project_manager: Mapped[Employee] = relationship(
        "Employee", foreign_keys=[project_manager_id], back_populates="managed_projects"
    )
    client: Mapped[Client] = relationship("Client", back_populates="projects")
    team: Mapped[Team] = relationship("Team")
    created_by: Mapped[Employee] = relationship(
        "Employee", foreign_keys=[created_by_id], back_populates="created_projects"
    )
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="ck_project_dates"),
    )


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    assignee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    manday: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    budget: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Planned")

    project: Mapped[Project] = relationship("Project", back_populates="tasks")
    assignee: Mapped[Employee] = relationship("Employee", back_populates="assigned_tasks")
    task_activities: Mapped[List["TaskActivity"]] = relationship(
        "TaskActivity", back_populates="task", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("name", "project_id", name="uq_task_project_name"),
    )


class Month(Base):
    __tablename__ = "months"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    yyyy_mm: Mapped[str] = mapped_column(String(7), nullable=False, unique=True)

    task_activities: Mapped[List["TaskActivity"]] = relationship("TaskActivity", back_populates="month")


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    task_activities: Mapped[List["TaskActivity"]] = relationship("TaskActivity", back_populates="activity")


class TaskActivity(Base):
    __tablename__ = "task_activities"

    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    month_id: Mapped[int] = mapped_column(ForeignKey("months.id"), primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), primary_key=True)

    task: Mapped[Task] = relationship("Task", back_populates="task_activities")
    month: Mapped[Month] = relationship("Month", back_populates="task_activities")
    activity: Mapped[Activity] = relationship("Activity", back_populates="task_activities")

    __table_args__ = (
        UniqueConstraint("task_id", "month_id", "activity_id", name="uq_task_month_activity"),
    )
