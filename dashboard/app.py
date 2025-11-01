import os
from contextlib import contextmanager
from datetime import date
from typing import Any

import httpx
import pandas as pd
import plotly.express as px
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
PROJECT_STATUS_OPTIONS = [
    "planned",
    "active",
    "on_hold",
    "completed",
]
TASK_STATUS_OPTIONS = [
    "not_started",
    "in_progress",
    "at_risk",
    "blocked",
    "complete",
]


@contextmanager
def api_client() -> httpx.Client:
    client = httpx.Client(base_url=API_BASE_URL, timeout=15.0)
    try:
        yield client
    finally:
        client.close()


def api_request(method: str, path: str, **kwargs: Any) -> Any:
    with api_client() as client:
        response = client.request(method, path, **kwargs)
        response.raise_for_status()
        if response.status_code == 204:
            return None
        return response.json()


@st.cache_data(ttl=60)
def fetch_projects() -> list[dict[str, Any]]:
    return api_request("GET", "/projects/")


@st.cache_data(ttl=60)
def fetch_tasks(assignee: str | None = None, project_id: int | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    if assignee:
        params["assignee"] = assignee
    if project_id:
        params["project_id"] = project_id
    return api_request("GET", "/tasks/", params=params)


@st.cache_data(ttl=120)
def fetch_portfolio_summary() -> dict[str, Any]:
    return api_request("GET", "/metrics/portfolio")


@st.cache_data(ttl=120)
def fetch_team_utilization() -> list[dict[str, Any]]:
    return api_request("GET", "/metrics/team")


@st.cache_data(ttl=300)
def fetch_assignees() -> list[str]:
    return api_request("GET", "/tasks/assignees/list")


def invalidate_task_cache() -> None:
    fetch_tasks.clear()
    fetch_assignees.clear()


def invalidate_project_cache() -> None:
    fetch_projects.clear()
    invalidate_task_cache()
    fetch_portfolio_summary.clear()
    fetch_team_utilization.clear()


def team_member_view() -> None:
    st.subheader("Team Member Workspace")
    assignees = fetch_assignees()
    if not assignees:
        st.info("No assignees found. Check back after tasks have been created.")
        return

    selected_assignee = st.selectbox("Select your name", options=assignees)
    tasks = fetch_tasks(assignee=selected_assignee)

    if not tasks:
        st.info("No tasks assigned yet.")
        return

    for task in tasks:
        with st.expander(task["name"], expanded=False):
            st.write(
                f"**Project:** {task['project_id']} · **Timeline:** {task['start_date']} → {task.get('end_date') or 'TBD'}"
            )
            st.progress(task["progress"])
            progress_percent = int(task["progress"] * 100)
            new_progress = st.slider(
                "Progress (%)",
                min_value=0,
                max_value=100,
                value=progress_percent,
                key=f"progress-{task['id']}",
            )
            new_status = st.selectbox(
                "Status",
                options=TASK_STATUS_OPTIONS,
                index=TASK_STATUS_OPTIONS.index(task["status"]),
                key=f"status-{task['id']}",
            )
            new_remarks = st.text_area(
                "Remarks",
                value=task.get("remarks") or "",
                key=f"remarks-{task['id']}",
            )

            if st.button("Update Task", key=f"update-{task['id']}"):
                try:
                    api_request(
                        "PATCH",
                        f"/tasks/{task['id']}",
                        json={
                            "progress": round(new_progress / 100, 2),
                            "status": new_status,
                            "remarks": new_remarks or None,
                        },
                    )
                except httpx.HTTPError as exc:
                    st.error(f"Failed to update task: {exc}")
                else:
                    st.success("Task updated.")
                    invalidate_task_cache()
                    st.experimental_rerun()


def project_manager_view() -> None:
    st.subheader("Project Manager Console")

    with st.expander("Create a new project", expanded=False):
        with st.form("create_project"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Project Name", max_chars=255)
                client = st.text_input("Client Name", max_chars=255)
                project_manager = st.text_input("Project Manager", max_chars=255)
                start_date = st.date_input("Start Date", value=date.today())
            with col2:
                budget = st.number_input("Budget (USD)", min_value=0.0, step=1000.0)
                end_date = st.date_input("Target End Date", value=date.today())
                status = st.selectbox("Status", options=PROJECT_STATUS_OPTIONS, index=1)
            submitted = st.form_submit_button("Create Project")
            if submitted:
                payload = {
                    "name": name,
                    "client": client,
                    "project_manager": project_manager,
                    "budget": budget,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "status": status,
                }
                try:
                    api_request("POST", "/projects/", json=payload)
                except httpx.HTTPError as exc:
                    st.error(f"Project creation failed: {exc}")
                else:
                    st.success("Project created successfully.")
                    invalidate_project_cache()
                    st.experimental_rerun()

    projects = fetch_projects()
    if not projects:
        st.info("No projects found. Create one above to get started.")
        return

    project_df = pd.DataFrame(projects)
    st.dataframe(project_df[["id", "name", "client", "project_manager", "status"]], use_container_width=True)

    selected_project = st.selectbox(
        "Choose a project to manage tasks",
        options=[project["id"] for project in projects],
        format_func=lambda project_id: next(p["name"] for p in projects if p["id"] == project_id),
    )

    project_tasks = fetch_tasks(project_id=selected_project)
    st.markdown("### Task Overview")
    if project_tasks:
        task_df = pd.DataFrame(project_tasks)
        task_df["progress_pct"] = (task_df["progress"] * 100).round(0)
        st.dataframe(
            task_df[
                ["id", "name", "assignee", "man_days", "status", "progress_pct", "start_date", "end_date", "remarks"]
            ].rename(columns={"progress_pct": "progress (%)"}),
            use_container_width=True,
        )
    else:
        st.info("There are no tasks for this project yet.")

    with st.expander("Create a new task", expanded=False):
        with st.form("create_task"):
            col1, col2 = st.columns(2)
            with col1:
                task_name = st.text_input("Task Name", key="task_name")
                assignee = st.text_input("Assignee", key="task_assignee")
                man_days = st.number_input("Estimated Man-days", min_value=0.0, step=0.5, key="task_days")
                status = st.selectbox("Status", TASK_STATUS_OPTIONS, index=0, key="task_status")
            with col2:
                start_date = st.date_input("Start Date", value=date.today(), key="task_start")
                end_date = st.date_input("End Date", value=date.today(), key="task_end")
                remarks = st.text_area("Remarks (Optional)", key="task_remarks")
            submitted = st.form_submit_button("Create Task")
            if submitted:
                payload = {
                    "project_id": selected_project,
                    "name": task_name,
                    "assignee": assignee,
                    "man_days": man_days,
                    "status": status,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "remarks": remarks or None,
                    "progress": 0.0,
                }
                try:
                    api_request("POST", "/tasks/", json=payload)
                except httpx.HTTPError as exc:
                    st.error(f"Task creation failed: {exc}")
                else:
                    st.success("Task added.")
                    invalidate_task_cache()
                    st.experimental_rerun()


def company_manager_view() -> None:
    st.subheader("Company Manager Dashboard")
    summary = fetch_portfolio_summary()

    metric_cols = st.columns(3)
    metric_cols[0].metric("Total Projects", summary["total_projects"])
    metric_cols[1].metric("Active Projects", summary["active_projects"])
    metric_cols[2].metric("Completed Projects", summary["completed_projects"])

    metric_cols = st.columns(3)
    metric_cols[0].metric("Total Man-days", f"{summary['total_man_days']:.1f}")
    metric_cols[1].metric("Completion Rate", f"{summary['overall_completion_rate'] * 100:.1f}%")
    metric_cols[2].metric("Budget Utilization", f"{summary['budget_utilization'] * 100:.1f}%")

    projects = fetch_projects()
    if projects:
        status_df = pd.DataFrame(projects)
        status_fig = px.pie(status_df, names="status", title="Project Status Distribution")
        st.plotly_chart(status_fig, use_container_width=True)

    utilization = fetch_team_utilization()
    if utilization:
        util_df = pd.DataFrame(utilization)
        utilization_chart = px.bar(
            util_df,
            x="assignee",
            y="man_days",
            color="tasks",
            labels={"man_days": "Total Man-days", "assignee": "Team Member", "tasks": "Total Tasks"},
            title="Resource Utilization by Team Member",
        )
        st.plotly_chart(utilization_chart, use_container_width=True)
    else:
        st.info("No utilization data available.")


def main() -> None:
    st.set_page_config(page_title="Creagy Project Tracker", layout="wide")
    st.title("Creagy Project Tracker")
    st.caption("Role-based workspace for internal consulting and research teams")

    tabs = st.tabs(["Team Member", "Project Manager", "Company Manager"])

    with tabs[0]:
        try:
            team_member_view()
        except httpx.HTTPError as exc:
            st.error(f"Unable to load team member view: {exc}")

    with tabs[1]:
        try:
            project_manager_view()
        except httpx.HTTPError as exc:
            st.error(f"Unable to load project manager view: {exc}")

    with tabs[2]:
        try:
            company_manager_view()
        except httpx.HTTPError as exc:
            st.error(f"Unable to load company manager view: {exc}")


if __name__ == "__main__":
    main()
