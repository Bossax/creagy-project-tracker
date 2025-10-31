"""Utility helpers for automation scripts in the Creagy project tracker."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
import json
from pathlib import Path
from typing import Iterable, Sequence

from sqlalchemy.orm import Session

try:
    from backend import crud
    from backend import models
except ModuleNotFoundError as exc:  # pragma: no cover - runtime configuration guard
    raise ModuleNotFoundError(
        "Backend modules could not be imported. Ensure the repository root is on sys.path"
    ) from exc


@dataclass(slots=True)
class TaskRecord:
    """Normalised representation of a task for reporting utilities."""

    id: int | None
    name: str
    owner: str | None = None
    status: str | None = None
    due_date: date | None = None
    notes: str | None = None


@dataclass(slots=True)
class ProjectRecord:
    """Normalised representation of a project with nested tasks."""

    id: int | None
    name: str
    owner: str | None = None
    status: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    notes: str | None = None
    budget_allocated: float | None = None
    budget_spent: float | None = None
    tasks: list[TaskRecord] = field(default_factory=list)


def _coerce_date(value: object) -> date | None:
    """Return :class:`datetime.date` for the supplied value if possible."""

    if value in (None, "", "null"):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _safe_float(value: object) -> float | None:
    """Attempt to convert a value into a float, returning ``None`` on failure."""

    if value in (None, "", "null"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _task_from_mapping(payload: dict) -> TaskRecord:
    """Create a :class:`TaskRecord` from a serialised mapping."""

    return TaskRecord(
        id=payload.get("id"),
        name=str(payload.get("name", "Unnamed task")),
        owner=payload.get("owner"),
        status=payload.get("status"),
        due_date=_coerce_date(payload.get("due_date")),
        notes=payload.get("notes"),
    )


def project_from_mapping(payload: dict) -> ProjectRecord:
    """Create a :class:`ProjectRecord` from a serialised mapping."""

    tasks = [_task_from_mapping(task) for task in payload.get("tasks", [])]
    return ProjectRecord(
        id=payload.get("id"),
        name=str(payload.get("name", "Unnamed project")),
        owner=payload.get("owner"),
        status=payload.get("status"),
        start_date=_coerce_date(payload.get("start_date")),
        end_date=_coerce_date(payload.get("end_date")),
        notes=payload.get("notes"),
        budget_allocated=_safe_float(payload.get("budget_allocated")),
        budget_spent=_safe_float(payload.get("budget_spent")),
        tasks=tasks,
    )


def project_from_model(project: models.Project) -> ProjectRecord:
    """Normalise a SQLAlchemy project model into a :class:`ProjectRecord`."""

    tasks = [
        TaskRecord(
            id=task.id,
            name=task.name,
            owner=task.owner,
            status=task.status,
            due_date=_coerce_date(task.due_date),
            notes=task.notes,
        )
        for task in project.tasks
    ]

    return ProjectRecord(
        id=project.id,
        name=project.name,
        owner=project.owner,
        status=project.status,
        start_date=_coerce_date(project.start_date),
        end_date=_coerce_date(project.end_date),
        notes=project.notes,
        budget_allocated=_safe_float(project.budget_allocated),
        budget_spent=_safe_float(project.budget_spent),
        tasks=tasks,
    )


def fetch_projects_from_db(session: Session) -> list[ProjectRecord]:
    """Return all projects from the database, including their tasks."""

    projects = crud.get_projects(session)
    return [project_from_model(project) for project in projects]


def load_projects_from_export(path: str | Path) -> list[ProjectRecord]:
    """Load projects from a dashboard export file.

    The dashboard currently exports data as JSON containing an array of
    projects with embedded tasks. The helper supports both file paths and
    :class:`pathlib.Path` objects and will raise :class:`ValueError` if the
    payload cannot be parsed.
    """

    export_path = Path(path)
    if not export_path.exists():
        msg = f"Dashboard export not found: {export_path}"
        raise FileNotFoundError(msg)

    with export_path.open("r", encoding="utf-8") as handle:
        try:
            payload = json.load(handle)
        except json.JSONDecodeError as exc:
            msg = f"Unable to parse dashboard export {export_path}: {exc}"
            raise ValueError(msg) from exc

    if not isinstance(payload, list):
        msg = "Dashboard export is expected to contain a list of projects"
        raise ValueError(msg)

    return [project_from_mapping(project) for project in payload]


def compute_status_breakdown(tasks: Sequence[TaskRecord]) -> dict[str, int]:
    """Return the number of tasks in each status category."""

    counter = Counter(task.status or "Unknown" for task in tasks)
    return dict(counter)


def compute_completion_percentage(tasks: Sequence[TaskRecord]) -> float:
    """Return completion percentage based on tasks marked as ``Completed``."""

    if not tasks:
        return 0.0
    breakdown = compute_status_breakdown(tasks)
    completed = breakdown.get("Completed", 0)
    return round((completed / len(tasks)) * 100, 2)


def upcoming_tasks(tasks: Iterable[TaskRecord], *, limit: int = 5) -> list[TaskRecord]:
    """Return tasks with a due date on or after today ordered by due date."""

    today = date.today()
    upcoming = [task for task in tasks if task.due_date and task.due_date >= today]
    upcoming.sort(key=lambda task: task.due_date)
    return upcoming[:limit]


def budget_summary(project: ProjectRecord) -> dict[str, float]:
    """Return allocated, spent, and remaining budget values for a project."""

    allocated = float(project.budget_allocated or 0.0)
    spent = float(project.budget_spent or 0.0)
    remaining = max(allocated - spent, 0.0)
    return {"allocated": allocated, "spent": spent, "remaining": remaining}


def summarise_project(project: ProjectRecord) -> dict[str, object]:
    """Return a serialisable summary for a project suitable for reporting."""

    tasks = list(project.tasks)
    breakdown = compute_status_breakdown(tasks)
    completion = compute_completion_percentage(tasks)
    budget = budget_summary(project)
    upcoming = upcoming_tasks(tasks)

    return {
        "project_id": project.id,
        "project_name": project.name,
        "owner": project.owner,
        "status": project.status,
        "completion_percentage": completion,
        "status_breakdown": breakdown,
        "budget": budget,
        "upcoming_tasks": upcoming,
        "notes": project.notes,
        "total_tasks": len(tasks),
    }


__all__ = [
    "TaskRecord",
    "ProjectRecord",
    "fetch_projects_from_db",
    "load_projects_from_export",
    "project_from_mapping",
    "project_from_model",
    "compute_status_breakdown",
    "compute_completion_percentage",
    "upcoming_tasks",
    "budget_summary",
    "summarise_project",
]
