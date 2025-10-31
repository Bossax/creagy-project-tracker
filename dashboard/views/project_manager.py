"""Project manager specific dashboard views."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any, Callable, Iterable, Mapping

import streamlit as st

from ..api_client import APIClient, APIClientError

StatusNormaliser = Callable[[str | None], str]
OwnerNormaliser = Callable[[str | None], str]

_STATUS_CHOICES: tuple[str, ...] = (
    "Planning",
    "In Progress",
    "On Hold",
    "Completed",
    "Archived",
)

_TASK_STATUS_CHOICES: tuple[str, ...] = (
    "Not Started",
    "In Progress",
    "Blocked",
    "Completed",
)


def _format_currency(value: float) -> str:
    """Return a succinct currency formatted string."""

    if value >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value/1_000:.1f}K"
    return f"${value:,.0f}"


def _vega_bar(values: Iterable[Mapping[str, Any]], *, x: str, y: str, title: str) -> None:
    """Render a small Vega-Lite bar chart inline."""

    spec = {
        "data": {"values": list(values)},
        "mark": {"type": "bar", "tooltip": True},
        "encoding": {
            "x": {"field": x, "type": "nominal", "sort": "-y"},
            "y": {"field": y, "type": "quantitative"},
            "color": {"field": x, "type": "nominal", "legend": None},
        },
        "title": title,
    }
    st.vega_lite_chart(spec, use_container_width=True)


def _parse_date_input(value: str) -> str | None:
    """Validate a YYYY-MM-DD string and return its ISO representation."""

    text = value.strip()
    if not text:
        return None
    return datetime.fromisoformat(text).date().isoformat()


def _select_index(value: str | None, choices: tuple[str, ...]) -> int:
    """Return the index of ``value`` in ``choices`` or 0 when missing."""

    if value and value in choices:
        return choices.index(value)
    return 0


def _build_project_payload(
    *,
    name: str,
    owner: str,
    status: str,
    start_date: str,
    end_date: str,
    notes: str,
    budget_allocated: float,
    budget_spent: float,
) -> dict[str, Any]:
    """Prepare the payload used for project create/update requests."""

    payload: dict[str, Any] = {"name": name.strip()}
    payload["owner"] = owner.strip() or None
    payload["status"] = status.strip() or None
    payload["notes"] = notes.strip() or None
    payload["budget_allocated"] = float(max(budget_allocated, 0.0))
    payload["budget_spent"] = float(max(budget_spent, 0.0))

    start_iso = _parse_date_input(start_date)
    end_iso = _parse_date_input(end_date)
    if start_iso:
        payload["start_date"] = start_iso
    if end_iso:
        payload["end_date"] = end_iso
    return payload


def _build_task_payload(
    *,
    name: str,
    owner: str,
    status: str,
    due_date: str,
    notes: str,
    project_id: int,
) -> dict[str, Any]:
    """Prepare the payload used for task create/update requests."""

    payload: dict[str, Any] = {"name": name.strip(), "project_id": project_id}
    payload["owner"] = owner.strip() or None
    payload["status"] = status.strip() or None
    payload["notes"] = notes.strip() or None

    due_iso = _parse_date_input(due_date)
    if due_iso:
        payload["due_date"] = due_iso
    return payload


def _find_project_by_label(
    label: str, project_lookup: Mapping[str, Mapping[str, Any]], default: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Return the project matching the provided label."""

    try:
        return project_lookup[label]
    except KeyError:  # pragma: no cover - defensive fallback
        return default


def render_project_manager_view(
    project_items: list[Mapping[str, Any]],
    task_items: list[Mapping[str, Any]],
    *,
    controls_container: Any,
    api_client: APIClient,
    normalise_owner: OwnerNormaliser,
    normalise_status: StatusNormaliser,
) -> None:
    """Render the dashboard view for project managers."""

    st.subheader("Project Oversight & Planning")

    with st.expander("Create a new project", expanded=not project_items):
        with st.form("pm-create-project"):
            new_name = st.text_input("Project name", placeholder="Website Redesign")
            new_owner = st.text_input("Project owner", placeholder="Alice Johnson")
            new_status = st.selectbox("Status", _STATUS_CHOICES, index=0)
            new_start = st.text_input("Start date", placeholder="YYYY-MM-DD")
            new_end = st.text_input("End date", placeholder="YYYY-MM-DD")
            new_budget_allocated = st.number_input(
                "Budget allocated ($)", min_value=0.0, step=1000.0, value=0.0
            )
            new_budget_spent = st.number_input(
                "Budget spent ($)", min_value=0.0, step=1000.0, value=0.0
            )
            new_notes = st.text_area("Notes", placeholder="Key objectives, risks, or context.")
            create_submitted = st.form_submit_button("Create project")

        if create_submitted:
            if not new_name.strip():
                st.error("Project name is required.")
            else:
                try:
                    payload = _build_project_payload(
                        name=new_name,
                        owner=new_owner,
                        status=new_status,
                        start_date=new_start,
                        end_date=new_end,
                        notes=new_notes,
                        budget_allocated=new_budget_allocated,
                        budget_spent=new_budget_spent,
                    )
                except ValueError:
                    st.error("Dates must be provided in YYYY-MM-DD format.")
                else:
                    try:
                        api_client.create_project(payload)
                    except APIClientError as exc:
                        st.error(f"Failed to create project: {exc}")
                    else:
                        st.success(f"Project '{new_name}' created.")
                        st.cache_data.clear()
                        st.experimental_rerun()

    if not project_items:
        st.info(
            "Projects will appear here once they are created or loaded from the backend service."
        )
        return

    project_lookup = {
        f"#{project.get('id', '?')} · {project.get('name', 'Project')}": project
        for project in project_items
    }
    project_labels = list(project_lookup)
    selected_label = controls_container.selectbox("Active project", project_labels, index=0)
    selected_project = _find_project_by_label(selected_label, project_lookup, project_items[0])

    st.markdown(
        "Track scope, staffing, budgets, and task completion for your project portfolio."
    )

    project_tasks = [
        task for task in task_items if task.get("project_id") == selected_project.get("id")
    ]

    project_id = selected_project.get("id")
    if project_id is None:
        st.error("Selected project is missing an identifier. Reload the page and try again.")
        return

    summary_cols = st.columns(4)
    summary_cols[0].metric("Status", selected_project.get("status", "Not set"))
    summary_cols[1].metric("Owner", selected_project.get("owner", "Unassigned"))
    summary_cols[2].metric("Tasks", len(project_tasks))

    allocated = float(selected_project.get("budget_allocated") or 0.0)
    spent = float(selected_project.get("budget_spent") or 0.0)
    summary_cols[3].metric(
        "Budget",
        f"{_format_currency(spent)} / {_format_currency(allocated)}",
    )

    st.markdown("### Delivery health")
    status_counts = Counter(normalise_status(task.get("status")) for task in project_tasks)
    if status_counts:
        _vega_bar(
            ({"Status": status, "Tasks": count} for status, count in status_counts.items()),
            x="Status",
            y="Tasks",
            title="Task progress",
        )
    else:
        st.warning("No tasks assigned yet—create tasks to monitor progress.")

    st.markdown("### Budget status")
    if allocated == 0:
        st.info("Set a budget to visualise utilisation trends.")
    _vega_bar(
        (
            {"Category": "Spent", "Amount": spent},
            {"Category": "Remaining", "Amount": max(allocated - spent, 0.0)},
        ),
        x="Category",
        y="Amount",
        title="Budget overview",
    )

    st.markdown("### Team workload")
    owner_counts = Counter(normalise_owner(task.get("owner")) for task in project_tasks)
    if owner_counts:
        _vega_bar(
            ({"Owner": owner, "Tasks": count} for owner, count in owner_counts.items()),
            x="Owner",
            y="Tasks",
            title="Assignments per team member",
        )
    else:
        st.info("Assign tasks to team members to balance workloads.")

    st.markdown("### Task list")
    if project_tasks:
        task_rows = [
            {
                "ID": task.get("id"),
                "Task": task.get("name"),
                "Owner": normalise_owner(task.get("owner")),
                "Status": normalise_status(task.get("status")),
                "Due": task.get("due_date") or "—",
            }
            for task in project_tasks
        ]
        st.dataframe(task_rows, hide_index=True, use_container_width=True)
    else:
        st.warning("No tasks linked to this project yet.")

    with st.expander("Edit selected project"):
        with st.form("pm-update-project"):
            name = st.text_input("Project name", value=selected_project.get("name", ""))
            owner = st.text_input("Project owner", value=selected_project.get("owner", ""))
            status = st.selectbox(
                "Status",
                _STATUS_CHOICES,
                index=_select_index(selected_project.get("status"), _STATUS_CHOICES),
            )
            start_date = st.text_input(
                "Start date",
                value=selected_project.get("start_date") or "",
                placeholder="YYYY-MM-DD",
            )
            end_date = st.text_input(
                "End date",
                value=selected_project.get("end_date") or "",
                placeholder="YYYY-MM-DD",
            )
            budget_allocated = st.number_input(
                "Budget allocated ($)",
                min_value=0.0,
                step=1000.0,
                value=float(selected_project.get("budget_allocated") or 0.0),
            )
            budget_spent = st.number_input(
                "Budget spent ($)",
                min_value=0.0,
                step=1000.0,
                value=float(selected_project.get("budget_spent") or 0.0),
            )
            notes = st.text_area("Notes", value=selected_project.get("notes") or "")
            update_submitted = st.form_submit_button("Save changes")

        if update_submitted:
            if not name.strip():
                st.error("Project name is required.")
            else:
                try:
                    payload = _build_project_payload(
                        name=name,
                        owner=owner,
                        status=status,
                        start_date=start_date,
                        end_date=end_date,
                        notes=notes,
                        budget_allocated=budget_allocated,
                        budget_spent=budget_spent,
                    )
                except ValueError:
                    st.error("Dates must be provided in YYYY-MM-DD format.")
                else:
                    try:
                        api_client.update_project(int(project_id), payload)
                    except APIClientError as exc:
                        st.error(f"Failed to update project: {exc}")
                    else:
                        st.success("Project updated.")
                        st.cache_data.clear()
                        st.experimental_rerun()

    with st.expander("Manage tasks"):
        with st.form("pm-create-task"):
            task_name = st.text_input("Task name", placeholder="Design landing page")
            task_owner = st.text_input("Task owner", placeholder="Carmen Diaz")
            task_status = st.selectbox("Status", _TASK_STATUS_CHOICES, index=0)
            task_due = st.text_input("Due date", placeholder="YYYY-MM-DD")
            task_notes = st.text_area("Notes", placeholder="Deliverables, risks, or context.")
            task_create_submitted = st.form_submit_button("Create task")

        if task_create_submitted:
            if not task_name.strip():
                st.error("Task name is required.")
            else:
                try:
                    payload = _build_task_payload(
                        name=task_name,
                        owner=task_owner,
                        status=task_status,
                        due_date=task_due,
                        notes=task_notes,
                        project_id=int(project_id),
                    )
                except ValueError:
                    st.error("Due date must be in YYYY-MM-DD format.")
                else:
                    try:
                        api_client.create_task(payload)
                    except APIClientError as exc:
                        st.error(f"Failed to create task: {exc}")
                    else:
                        st.success(f"Task '{task_name}' created.")
                        st.cache_data.clear()
                        st.experimental_rerun()

        if project_tasks:
            with st.form("pm-update-task"):
                task_lookup = {
                    f"#{task.get('id', '?')} · {task.get('name', 'Task')}": task
                    for task in project_tasks
                }
                task_labels = list(task_lookup)
                selected_task_label = st.selectbox("Task", task_labels)
                selected_task = task_lookup[selected_task_label]
                new_owner = st.text_input(
                    "Assign to",
                    value=selected_task.get("owner", ""),
                )
                new_status = st.selectbox(
                    "Status",
                    _TASK_STATUS_CHOICES,
                    index=_select_index(selected_task.get("status"), _TASK_STATUS_CHOICES),
                )
                new_due = st.text_input(
                    "Due date",
                    value=selected_task.get("due_date") or "",
                    placeholder="YYYY-MM-DD",
                )
                update_task_submitted = st.form_submit_button("Update task")

            if update_task_submitted:
                try:
                    payload = _build_task_payload(
                        name=selected_task.get("name", "Task"),
                        owner=new_owner,
                        status=new_status,
                        due_date=new_due,
                        notes=selected_task.get("notes") or "",
                        project_id=int(project_id),
                    )
                except ValueError:
                    st.error("Due date must be in YYYY-MM-DD format.")
                else:
                    try:
                        api_client.update_task(int(selected_task.get("id")), payload)
                    except APIClientError as exc:
                        st.error(f"Failed to update task: {exc}")
                    else:
                        st.success("Task updated.")
                        st.cache_data.clear()
                        st.experimental_rerun()

    st.markdown("### Weekly report")
    if st.button("Generate weekly report", key="pm-generate-report"):
        try:
            report = api_client.generate_project_report(int(project_id))
        except APIClientError as exc:
            st.error(f"Failed to generate report: {exc}")
        else:
            st.success("Report generated.")
            generated_at = datetime.fromisoformat(report["generated_at"]).strftime(
                "%Y-%m-%d %H:%M"
            )
            st.write(f"**Generated:** {generated_at}")
            st.write(f"**Completion:** {report['completion_percentage']}%")

            st.write("#### Status breakdown")
            status_rows = [
                {"Status": status, "Tasks": count}
                for status, count in report.get("status_breakdown", {}).items()
            ]
            if status_rows:
                st.table(status_rows)
            else:
                st.info("No tasks available for this project yet.")

            upcoming = report.get("upcoming_tasks", [])
            if upcoming:
                st.write("#### Upcoming tasks")
                st.table(
                    [
                        {
                            "Task": task.get("name"),
                            "Owner": task.get("owner") or "Unassigned",
                            "Status": task.get("status") or "Unknown",
                            "Due": task.get("due_date") or "—",
                        }
                        for task in upcoming
                    ]
                )

            summary_lines = [
                f"Weekly report for {report['project_name']} ({generated_at})",
                "",
                f"Completion: {report['completion_percentage']}%",
                "Status breakdown:",
            ]
            for status, count in report.get("status_breakdown", {}).items():
                summary_lines.append(f"  - {status}: {count}")
            summary_lines.append(
                f"Budget: ${report['budget']['spent']:,.0f} spent / ${report['budget']['allocated']:,.0f} allocated"
            )
            if report.get("notes"):
                summary_lines.extend(("", "Notes:", report["notes"]))

            report_text = "\n".join(summary_lines)
            st.download_button(
                "Download report",
                report_text.encode("utf-8"),
                file_name="weekly-report.txt",
            )
