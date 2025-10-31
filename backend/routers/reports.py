"""Reporting endpoints exposing aggregated portfolio insights."""
from __future__ import annotations

from collections import Counter
from typing import Iterable, Sequence

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud, models, schemas
from ..database import get_session

router = APIRouter(prefix="/reports", tags=["Reports"])

_MAN_DAY_KEYS: tuple[str, ...] = (
    "estimated_man_days",
    "man_days",
    "estimate_days",
    "effort_days",
)


def _normalise_status(value: str | None) -> str:
    """Return a consistent, human-readable status string."""

    if not value:
        return "Unknown"
    text = value.replace("_", " ").strip()
    return text.title() if text else "Unknown"


def _is_active_status(status: str) -> bool:
    """Determine if a project should be considered active."""

    return status not in {"Completed", "Archived"}


def _extract_man_days(task: models.Task) -> float:
    """Determine the man-day estimate for a task with sensible defaults."""

    for key in _MAN_DAY_KEYS:
        value = getattr(task, key, None)
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:  # pragma: no cover - defensive
                continue
    return 1.0


def compute_portfolio_report(
    projects: Sequence[models.Project] | Iterable[models.Project],
) -> schemas.PortfolioReport:
    """Build the aggregated portfolio report from project ORM objects."""

    project_list = list(projects)
    project_count = len(project_list)
    all_tasks = [task for project in project_list for task in list(project.tasks)]

    project_status_counts = Counter(
        _normalise_status(project.status) for project in project_list
    )
    task_status_counts = Counter(_normalise_status(task.status) for task in all_tasks)

    active_projects = sum(
        1 for project in project_list if _is_active_status(_normalise_status(project.status))
    )

    allocated_total = sum(float(project.budget_allocated or 0.0) for project in project_list)
    spent_total = sum(float(project.budget_spent or 0.0) for project in project_list)
    remaining_total = max(allocated_total - spent_total, 0.0)
    utilisation = 0.0
    if allocated_total:
        utilisation = min((spent_total / allocated_total) * 100, 100.0)

    project_health = [
        schemas.ProjectHealthBreakdown(status=status, projects=count)
        for status, count in sorted(
            project_status_counts.items(), key=lambda item: (-item[1], item[0])
        )
    ]

    task_status = [
        schemas.TaskStatusBreakdown(status=status, tasks=count)
        for status, count in sorted(task_status_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    progress_entries: list[schemas.ProjectProgressSummary] = []
    man_day_entries: list[schemas.ManDayAllocation] = []

    for project in project_list:
        tasks = list(project.tasks)
        total_tasks = len(tasks)
        completed_tasks = sum(
            1 for task in tasks if _normalise_status(task.status) == "Completed"
        )
        completion_percentage = (completed_tasks / total_tasks * 100) if total_tasks else 0.0

        project_name = project.name or f"Project #{project.id or '?'}"
        project_id = project.id or 0

        progress_entries.append(
            schemas.ProjectProgressSummary(
                project_id=project_id,
                project_name=project_name,
                status=_normalise_status(project.status),
                completion_percentage=round(completion_percentage, 2),
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
            )
        )

        man_days = sum(_extract_man_days(task) for task in tasks)
        man_day_entries.append(
            schemas.ManDayAllocation(
                project_id=project_id,
                project_name=project_name,
                man_days=round(man_days, 2),
            )
        )

    progress_entries.sort(key=lambda entry: entry.completion_percentage, reverse=True)
    man_day_entries.sort(key=lambda entry: entry.man_days, reverse=True)

    report = schemas.PortfolioReport(
        project_count=project_count,
        active_projects=active_projects,
        total_tasks=len(all_tasks),
        budget=schemas.PortfolioBudgetSummary(
            allocated=round(allocated_total, 2),
            spent=round(spent_total, 2),
            remaining=round(remaining_total, 2),
            utilisation=round(utilisation, 2),
        ),
        project_health=project_health,
        task_status=task_status,
        project_progress=progress_entries,
        man_day_allocation=man_day_entries,
    )
    return report


@router.get("/portfolio", response_model=schemas.PortfolioReport)
def get_portfolio_report(db: Session = Depends(get_session)) -> schemas.PortfolioReport:
    """Return aggregated metrics for the entire delivery portfolio."""

    projects = crud.get_projects(db)
    return compute_portfolio_report(projects)


__all__ = ["router", "compute_portfolio_report"]

