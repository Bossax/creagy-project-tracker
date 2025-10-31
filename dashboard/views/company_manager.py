"""Company manager specific dashboard view components."""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

import streamlit as st

PortfolioReport = Mapping[str, Any]


def _format_currency(value: float) -> str:
    """Return a compact currency representation for dashboard metrics."""

    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:,.0f}"


def _normalise_status(value: str | None) -> str:
    """Return a consistent status label for fallback aggregations."""

    if not value:
        return "Unknown"
    text = value.replace("_", " ").strip()
    return text.title() if text else "Unknown"


def _extract_tasks_from_project(project: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    """Return associated tasks embedded within project payloads."""

    tasks = project.get("tasks")
    if isinstance(tasks, Sequence) and not isinstance(tasks, (str, bytes)):
        return tasks  # type: ignore[return-value]
    return []


def _build_fallback_portfolio_report(
    project_items: Sequence[Mapping[str, Any]],
    task_items: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Create a lightweight portfolio summary when the API aggregation is unavailable."""

    project_status_counts: dict[str, int] = {}
    for project in project_items:
        status = _normalise_status(project.get("status"))
        project_status_counts[status] = project_status_counts.get(status, 0) + 1

    task_status_counts: dict[str, int] = {}
    for task in task_items:
        status = _normalise_status(task.get("status"))
        task_status_counts[status] = task_status_counts.get(status, 0) + 1

    project_progress: list[dict[str, Any]] = []
    man_day_allocation: list[dict[str, Any]] = []

    for project in project_items:
        tasks = list(_extract_tasks_from_project(project))
        total_tasks = len(tasks)
        completed_tasks = sum(
            1 for task in tasks if _normalise_status(task.get("status")) == "Completed"
        )
        completion = (completed_tasks / total_tasks * 100) if total_tasks else 0.0

        project_progress.append(
            {
                "project_id": project.get("id", 0),
                "project_name": project.get("name", "Project"),
                "status": _normalise_status(project.get("status")),
                "completion_percentage": round(completion, 2),
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
            }
        )

        man_day_allocation.append(
            {
                "project_id": project.get("id", 0),
                "project_name": project.get("name", "Project"),
                "man_days": float(total_tasks),
            }
        )

    project_progress.sort(key=lambda entry: entry["completion_percentage"], reverse=True)
    man_day_allocation.sort(key=lambda entry: entry["man_days"], reverse=True)

    allocated_total = sum(float(project.get("budget_allocated") or 0.0) for project in project_items)
    spent_total = sum(float(project.get("budget_spent") or 0.0) for project in project_items)
    remaining_total = max(allocated_total - spent_total, 0.0)
    utilisation = (spent_total / allocated_total * 100) if allocated_total else 0.0

    project_health = [
        {"status": status, "projects": count}
        for status, count in sorted(project_status_counts.items(), key=lambda item: (-item[1], item[0]))
    ]
    task_status = [
        {"status": status, "tasks": count}
        for status, count in sorted(task_status_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    report = {
        "project_count": len(project_items),
        "active_projects": sum(
            1
            for project in project_items
            if _normalise_status(project.get("status")) not in {"Completed", "Archived"}
        ),
        "total_tasks": len(task_items),
        "budget": {
            "allocated": round(allocated_total, 2),
            "spent": round(spent_total, 2),
            "remaining": round(remaining_total, 2),
            "utilisation": round(utilisation, 2),
        },
        "project_health": project_health,
        "task_status": task_status,
        "project_progress": project_progress,
        "man_day_allocation": man_day_allocation,
    }
    return report


def _vega_bar(
    values: Iterable[Mapping[str, Any]],
    *,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    sort: str | None = "-x",
) -> None:
    """Render a Vega-Lite bar chart for the provided values."""

    spec: dict[str, Any] = {
        "data": {"values": list(values)},
        "mark": {"type": "bar", "tooltip": True},
        "encoding": {
            "x": {"field": x, "type": "quantitative" if x != "status" else "nominal"},
            "y": {"field": y, "type": "nominal", "sort": sort},
        },
        "title": title,
    }
    if color:
        spec["encoding"]["color"] = {"field": color, "type": "nominal"}
    st.vega_lite_chart(spec, use_container_width=True)


def _vega_column(
    values: Iterable[Mapping[str, Any]],
    *,
    category: str,
    metric: str,
    title: str,
) -> None:
    """Render a Vega-Lite column chart."""

    spec = {
        "data": {"values": list(values)},
        "mark": {"type": "bar", "tooltip": True},
        "encoding": {
            "x": {"field": category, "type": "nominal", "sort": "-y"},
            "y": {"field": metric, "type": "quantitative"},
            "color": {"field": category, "type": "nominal", "legend": None},
        },
        "title": title,
    }
    st.vega_lite_chart(spec, use_container_width=True)


def render_company_manager_view(
    project_items: Sequence[Mapping[str, Any]],
    task_items: Sequence[Mapping[str, Any]],
    *,
    portfolio_report: PortfolioReport | None,
) -> None:
    """Render the dashboard view for company leadership roles."""

    st.subheader("Portfolio Performance Dashboard")
    if not project_items:
        st.info("Create or load projects to unlock portfolio-level insights.")
        return

    if portfolio_report is None:
        portfolio_report = _build_fallback_portfolio_report(project_items, task_items)
        st.caption(
            "Fallback metrics are calculated from the projects currently loaded in the UI."
        )

    summary_cols = st.columns(4)
    summary_cols[0].metric("Projects", portfolio_report.get("project_count", 0))
    summary_cols[1].metric("Active", portfolio_report.get("active_projects", 0))
    summary_cols[2].metric("Tasks", portfolio_report.get("total_tasks", 0))
    utilisation = portfolio_report.get("budget", {}).get("utilisation", 0.0)
    summary_cols[3].metric("Budget Utilisation", f"{utilisation:.1f}%")

    budget = portfolio_report.get("budget", {})
    budget_cols = st.columns(3)
    budget_cols[0].metric(
        "Allocated", _format_currency(float(budget.get("allocated", 0.0)))
    )
    budget_cols[1].metric("Spent", _format_currency(float(budget.get("spent", 0.0))))
    budget_cols[2].metric(
        "Remaining", _format_currency(float(budget.get("remaining", 0.0)))
    )

    st.markdown("### Project Health")
    project_health = portfolio_report.get("project_health", [])
    if project_health:
        _vega_column(project_health, category="status", metric="projects", title="Projects by Status")
    else:
        st.info("No project status data available yet.")

    st.markdown("### Task Delivery Pipeline")
    task_status = portfolio_report.get("task_status", [])
    if task_status:
        _vega_column(task_status, category="status", metric="tasks", title="Tasks by Status")
    else:
        st.info("Task status information will appear once tasks are recorded.")

    st.markdown("### Project Progress Comparison")
    progress_entries = portfolio_report.get("project_progress", [])
    if progress_entries:
        _vega_bar(
            progress_entries,
            x="completion_percentage",
            y="project_name",
            title="Completion Percentage",
            color="status",
        )
        progress_table = [
            {
                "Project": entry.get("project_name", "Project"),
                "Status": entry.get("status", "Unknown"),
                "Completed": f"{entry.get('completed_tasks', 0)}/{entry.get('total_tasks', 0)}",
                "Completion %": f"{entry.get('completion_percentage', 0.0):.1f}",
            }
            for entry in progress_entries
        ]
        st.dataframe(progress_table, hide_index=True, use_container_width=True)
    else:
        st.info("Progress metrics will populate as tasks are completed.")

    st.markdown("### Man-day Allocation by Project")
    man_day_entries = portfolio_report.get("man_day_allocation", [])
    if man_day_entries:
        _vega_bar(
            man_day_entries,
            x="man_days",
            y="project_name",
            title="Estimated Man-days",
        )
    else:
        st.info("Man-day allocation data is not available for the current projects.")


__all__ = ["render_company_manager_view"]

