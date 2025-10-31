"""Tests for Pydantic schemas."""
from __future__ import annotations

from datetime import date

import pytest
from pydantic import ValidationError

from backend import models, schemas


def test_project_create_requires_name() -> None:
    """ProjectCreate should validate the required name field."""

    with pytest.raises(ValidationError):
        schemas.ProjectCreate()  # type: ignore[call-arg]


def test_project_schema_from_orm() -> None:
    """Project schema should support loading from SQLAlchemy objects."""

    project = models.Project(
        id=1,
        name="New Website",
        owner="Alice",
        status="active",
        start_date=date(2024, 1, 1),
        end_date=date(2024, 6, 30),
        notes="Important client",
    )
    task = models.Task(
        id=10,
        project_id=1,
        name="Design mockups",
        owner="Bob",
        status="in_progress",
        due_date=date(2024, 2, 15),
        notes="Coordinate with design team",
    )
    project.tasks.append(task)

    schema = schemas.Project.model_validate(project)

    assert schema.id == 1
    assert schema.name == "New Website"
    assert schema.tasks[0].name == "Design mockups"
    assert schema.tasks[0].project_id == 1
