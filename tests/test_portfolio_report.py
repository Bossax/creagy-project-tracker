from __future__ import annotations

from backend.models import Project, Task
from backend.routers.reports import compute_portfolio_report


def _build_project(
    project_id: int,
    *,
    name: str,
    status: str,
    budget_allocated: float,
    budget_spent: float,
    task_statuses: list[str],
) -> Project:
    project = Project(
        id=project_id,
        name=name,
        status=status,
        budget_allocated=budget_allocated,
        budget_spent=budget_spent,
    )
    for index, task_status in enumerate(task_statuses, start=1):
        task = Task(
            id=project_id * 100 + index,
            project_id=project_id,
            name=f"Task {index}",
            status=task_status,
        )
        project.tasks.append(task)
    return project


def test_compute_portfolio_report_aggregates_core_metrics() -> None:
    """Portfolio report should aggregate project, budget, and task metrics."""

    project_alpha = _build_project(
        1,
        name="Alpha",
        status="In Progress",
        budget_allocated=100_000,
        budget_spent=25_000,
        task_statuses=["Completed", "In Progress", "Not Started"],
    )
    project_beta = _build_project(
        2,
        name="Beta",
        status="Completed",
        budget_allocated=50_000,
        budget_spent=45_000,
        task_statuses=["Completed", "Completed"],
    )

    report = compute_portfolio_report([project_alpha, project_beta])

    assert report.project_count == 2
    assert report.active_projects == 1  # Only Alpha is still active
    assert report.total_tasks == 5
    assert report.budget.allocated == 150_000
    assert report.budget.spent == 70_000
    assert report.budget.remaining == 80_000
    assert report.budget.utilisation == 46.67

    health_lookup = {entry.status: entry.projects for entry in report.project_health}
    assert health_lookup["In Progress"] == 1
    assert health_lookup["Completed"] == 1

    task_lookup = {entry.status: entry.tasks for entry in report.task_status}
    assert task_lookup["Completed"] == 3
    assert task_lookup["In Progress"] == 1

    progress_lookup = {entry.project_name: entry for entry in report.project_progress}
    assert progress_lookup["Alpha"].completion_percentage == 33.33
    assert progress_lookup["Beta"].completion_percentage == 100.0

    man_day_lookup = {entry.project_name: entry.man_days for entry in report.man_day_allocation}
    assert man_day_lookup["Alpha"] == 3.0
    assert man_day_lookup["Beta"] == 2.0
