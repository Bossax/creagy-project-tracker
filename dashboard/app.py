"""Streamlit dashboard entrypoint for the Creagy project tracker."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import streamlit as st

if __package__ in (None, ""):
    sys.path.append(str(Path(__file__).resolve().parent.parent))
    from dashboard.api_client import APIClient, APIClientError  # type: ignore[import-not-found]
    from dashboard.views import (  # type: ignore[import-not-found]
        render_company_manager_view,
        render_project_manager_view,
        render_team_member_view,
    )
else:
    from .api_client import APIClient, APIClientError
    from .views import (
        render_company_manager_view,
        render_project_manager_view,
        render_team_member_view,
    )

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


@st.cache_data(ttl=60, show_spinner=False)
def fetch_portfolio_report(base_url: str, timeout: float) -> dict[str, Any]:
    """Load aggregated portfolio metrics from the backend service."""

    return APIClient(base_url=base_url, timeout=timeout).portfolio_report()


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

portfolio_report: dict[str, Any] | None = None
portfolio_error: str | None = None
try:
    portfolio_report = fetch_portfolio_report(client.base_url, client.timeout)
except APIClientError as exc:
    portfolio_error = str(exc)

def normalise_owner(value: str | None) -> str:
    """Return a safe representation for task owners."""

    return value or "Unassigned"


def normalise_status(value: str | None) -> str:
    """Return a safe representation for task statuses."""

    return value or "Unknown"

if projects_error:
    st.warning(
        "Projects could not be loaded from the backend yet. "
        "Start the FastAPI service and refresh the page to populate data."
    )

if role == "Team Member":
    render_team_member_view(
        tasks,
        controls_container=role_controls,
        api_client=client,
        normalise_owner=normalise_owner,
        normalise_status=normalise_status,
    )
elif role == "Project Manager":
    render_project_manager_view(
        projects,
        tasks,
        controls_container=role_controls,
        api_client=client,
        normalise_owner=normalise_owner,
        normalise_status=normalise_status,
    )
else:
    if portfolio_error:
        st.warning(
            "Detailed portfolio aggregates are currently unavailable from the backend. "
            "Showing locally calculated figures instead."
        )
    render_company_manager_view(
        projects,
        tasks,
        portfolio_report=portfolio_report,
    )
