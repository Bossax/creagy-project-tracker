"""Streamlit dashboard entrypoint for the Creagy project tracker."""
from __future__ import annotations

from collections import Counter
from typing import Any

import streamlit as st

from api_client import APIClient, APIClientError

st.set_page_config(
    page_title="Creagy Project Tracker",
    page_icon="📊",
    layout="wide",
)

st.title("Creagy Project Tracker Dashboard")
st.caption("Role-tailored overview of projects, tasks, and company performance")

client = APIClient()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_projects(base_url: str, timeout: float) -> list[dict[str, Any]]:
    """Load all projects from the backend service."""

    return APIClient(base_url=base_url, timeout=timeout).list_projects()


@st.cache_data(ttl=60, show_spinner=False)
def fetch_tasks(base_url: str, timeout: float) -> list[dict[str, Any]]:
    """Load all tasks from the backend service."""

    return APIClient(base_url=base_url, timeout=timeout).list_tasks()


@st.cache_data(ttl=30, show_spinner=False)
def fetch_health(base_url: str, timeout: float) -> dict[str, Any]:
    """Fetch the backend health payload for quick diagnostics."""

    return APIClient(base_url=base_url, timeout=timeout).health()


sidebar = st.sidebar.container()
sidebar.header("Configuration")
sidebar.markdown(f"**Backend URL:** `{client.base_url}`")

health_placeholder = sidebar.empty()
try:
    health = fetch_health(client.base_url, client.timeout)
except APIClientError as exc:
    health_placeholder.error(f"Backend offline: {exc}")
    health = None
else:
    health_placeholder.success(f"Backend status: {health.get('status', 'unknown')}")

role_options = (
    "Team Member",
    "Project Manager",
    "Company Manager",
)
role = sidebar.radio("Select your role", role_options)
role_controls = sidebar.container()

projects: list[dict[str, Any]] = []
projects_error: str | None = None
try:
    projects = fetch_projects(client.base_url, client.timeout)
except APIClientError as exc:
    projects_error = str(exc)

try:
    tasks = fetch_tasks(client.base_url, client.timeout)
except APIClientError:
    # Fall back to tasks embedded within projects when the direct call fails.
    tasks = [task for project in projects for task in project.get("tasks", [])]
else:
    # When both endpoints are available, prefer the explicit task endpoint.
    if not tasks:
        tasks = [task for project in projects for task in project.get("tasks", [])]

def normalise_owner(value: str | None) -> str:
    """Return a safe representation for task owners."""

    return value or "Unassigned"


def normalise_status(value: str | None) -> str:
    """Return a safe representation for task statuses."""

    return value or "Unknown"


def render_team_member_view(task_items: list[dict[str, Any]]) -> None:
    """Render a focused workspace for individual contributors."""

    st.subheader("My Tasks")
    if not task_items:
        st.info("No tasks available yet. Create tasks via the FastAPI backend to populate the list.")
        return

    owners = sorted({normalise_owner(task.get("owner")) for task in task_items})
    selected_owner = role_controls.selectbox("Team member", owners)

    filtered_tasks = [task for task in task_items if normalise_owner(task.get("owner")) == selected_owner]

    st.markdown(
        "Use the filters below to prioritise work and follow upcoming deadlines. "
        "Additional views such as burndown charts or daily stand-ups can be layered on later."
    )

    if filtered_tasks:
        status_counter = Counter(normalise_status(task.get("status")) for task in filtered_tasks)
        cols = st.columns(3)
        for idx, label in enumerate(["In Progress", "Blocked", "Completed"]):
            cols[idx % 3].metric(label, status_counter.get(label, 0))

        st.dataframe(filtered_tasks, hide_index=True)
    else:
        st.warning("No tasks match the selected filters just yet.")


def render_project_manager_view(project_items: list[dict[str, Any]], task_items: list[dict[str, Any]]) -> None:
    """Render an overview tailored to project managers."""

    st.subheader("Project Oversight")
    if not project_items:
        st.info("Projects will appear here once they are created in the backend service.")
        return

    project_lookup = {
        f"#{project.get('id', '?')} · {project.get('name', 'Project')}": project
        for project in project_items
    }
    project_name = role_controls.selectbox("Active project", list(project_lookup))
    selected_project = project_lookup.get(project_name, {})

    st.markdown(
        "Track scope, staffing, and task completion for each project. Future iterations can "
        "add burndown charts, sprint reports, or integrations with planning tools."
    )

    cols = st.columns(3)
    cols[0].metric("Status", selected_project.get("status", "Not set"))
    cols[1].metric("Owner", selected_project.get("owner", "Unassigned"))

    start: str | None = selected_project.get("start_date")
    end: str | None = selected_project.get("end_date")
    schedule = "TBD"
    if start or end:
        start_date = start or "?"
        end_date = end or "?"
        schedule = f"{start_date} → {end_date}"
    cols[2].metric("Schedule", schedule)

    related_tasks = [task for task in task_items if task.get("project_id") == selected_project.get("id")]
    st.markdown("### Tasks")
    if related_tasks:
        st.dataframe(related_tasks, hide_index=True)
    else:
        st.warning("This project does not have any tasks assigned yet.")


def render_company_manager_view(project_items: list[dict[str, Any]], task_items: list[dict[str, Any]]) -> None:
    """Render a leadership summary across the organisation."""

    st.subheader("Portfolio Snapshot")
    if not project_items:
        st.info("Once multiple projects exist, aggregate insights for leadership will be shown here.")
        return

    project_status_counts = Counter(normalise_status(project.get("status")) for project in project_items)
    task_status_counts = Counter(normalise_status(task.get("status")) for task in task_items)

    cols = st.columns(3)
    cols[0].metric("Active Projects", project_status_counts.get("Active", 0))
    cols[1].metric("Total Projects", len(project_items))
    cols[2].metric("Total Tasks", len(task_items))

    st.markdown("### Project Status Overview")
    project_summary = [
        {"Status": status, "Projects": count} for status, count in project_status_counts.items()
    ]
    st.table(project_summary or [{"Status": "Unknown", "Projects": 0}])

    st.markdown("### Task Pipeline Health")
    task_summary = [
        {"Status": status, "Tasks": count} for status, count in task_status_counts.items()
    ]
    st.table(task_summary or [{"Status": "Unknown", "Tasks": 0}])

    st.markdown(
        "This view will evolve into company-wide forecasting and resource allocation analytics."
    )


if projects_error:
    st.warning(
        "Projects could not be loaded from the backend yet. "
        "Start the FastAPI service and refresh the page to populate data."
    )

if role == "Team Member":
    render_team_member_view(tasks)
elif role == "Project Manager":
    render_project_manager_view(projects, tasks)
else:
    render_company_manager_view(projects, tasks)
