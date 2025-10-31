"""SQLAlchemy ORM models for the Creagy project tracker."""
from __future__ import annotations

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Project(Base):
    """Represents a tracked project."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    budget_allocated = Column(Float, nullable=True)
    budget_spent = Column(Float, nullable=True)

    tasks = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class Task(Base):
    """Represents an individual task associated with a project."""

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=True)
    status = Column(String(50), nullable=True)
    due_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    project = relationship("Project", back_populates="tasks")
