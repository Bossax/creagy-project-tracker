"""End-to-end tests for FastAPI endpoints using an in-memory database."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_session
from backend.main import app


@pytest.fixture()
def client() -> TestClient:
    """Return a test client backed by an in-memory SQLite database."""

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_session():
        with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def _create_project(client: TestClient, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "AI Platform",
        "owner": "Ava",
        "status": "In Progress",
        "budget_allocated": 100_000,
        "budget_spent": 25_000,
    }
    payload.update(overrides)
    response = client.post("/projects/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_task(client: TestClient, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "name": "Initial Planning",
        "project_id": overrides.get("project_id"),
        "status": "Not Started",
    }
    payload.update(overrides)
    response = client.post("/tasks/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_fetch_project(client: TestClient) -> None:
    """Creating a project should make it available via collection and detail views."""

    project = _create_project(client)

    list_response = client.get("/projects/")
    assert list_response.status_code == 200
    projects = list_response.json()
    assert len(projects) == 1
    assert projects[0]["id"] == project["id"]
    assert projects[0]["name"] == "AI Platform"

    detail_response = client.get(f"/projects/{project['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["name"] == "AI Platform"

    not_found_response = client.get("/projects/999")
    assert not_found_response.status_code == 404


def test_weekly_report_highlights_upcoming_tasks(client: TestClient) -> None:
    """Weekly reports should surface future tasks and summarise budgets."""

    project = _create_project(
        client,
        name="Data Warehouse Refresh",
        budget_allocated=50_000,
        budget_spent=10_000,
    )
    project_id = project["id"]

    upcoming_due = (date.today() + timedelta(days=3)).isoformat()
    past_due = (date.today() - timedelta(days=5)).isoformat()

    _create_task(
        client,
        project_id=project_id,
        name="Design Architecture",
        status="Completed",
        due_date=past_due,
    )
    _create_task(
        client,
        project_id=project_id,
        name="Load Historical Data",
        status="In Progress",
        due_date=upcoming_due,
    )

    report_response = client.get(f"/projects/{project_id}/weekly-report")
    assert report_response.status_code == 200
    report = report_response.json()

    assert report["project_name"] == "Data Warehouse Refresh"
    assert report["budget"]["allocated"] == 50_000.0
    assert report["budget"]["remaining"] == 40_000.0
    assert report["completion_percentage"] == 50.0
    upcoming_tasks = report["upcoming_tasks"]
    assert len(upcoming_tasks) == 1
    assert upcoming_tasks[0]["name"] == "Load Historical Data"


def test_tasks_endpoint_supports_project_filter(client: TestClient) -> None:
    """Tasks list endpoint should filter results by project identifier."""

    alpha = _create_project(client, name="Alpha")
    beta = _create_project(client, name="Beta")

    _create_task(client, project_id=alpha["id"], name="Alpha Planning")
    _create_task(client, project_id=beta["id"], name="Beta Planning")

    all_tasks_response = client.get("/tasks/")
    assert all_tasks_response.status_code == 200
    assert {task["name"] for task in all_tasks_response.json()} == {
        "Alpha Planning",
        "Beta Planning",
    }

    filtered_response = client.get(f"/tasks/?project_id={alpha['id']}")
    assert filtered_response.status_code == 200
    tasks = filtered_response.json()
    assert len(tasks) == 1
    assert tasks[0]["project_id"] == alpha["id"]
    assert tasks[0]["name"] == "Alpha Planning"


def test_portfolio_report_endpoint_aggregates_metrics(client: TestClient) -> None:
    """Portfolio report endpoint should aggregate core delivery metrics."""

    alpha = _create_project(
        client,
        name="Alpha",
        status="In Progress",
        budget_allocated=120_000,
        budget_spent=60_000,
    )
    beta = _create_project(
        client,
        name="Beta",
        status="Completed",
        budget_allocated=80_000,
        budget_spent=80_000,
    )

    _create_task(client, project_id=alpha["id"], name="Design", status="Completed")
    _create_task(client, project_id=alpha["id"], name="Build", status="In Progress")
    _create_task(client, project_id=beta["id"], name="Launch", status="Completed")

    report_response = client.get("/reports/portfolio")
    assert report_response.status_code == 200
    report = report_response.json()

    assert report["project_count"] == 2
    assert report["active_projects"] == 1
    assert report["total_tasks"] == 3
    assert report["budget"]["allocated"] == 200_000.0
    assert report["budget"]["spent"] == 140_000.0

    project_health = {entry["status"]: entry["projects"] for entry in report["project_health"]}
    assert project_health["In Progress"] == 1
    assert project_health["Completed"] == 1

    task_status = {entry["status"]: entry["tasks"] for entry in report["task_status"]}
    assert task_status["Completed"] == 2
    assert task_status["In Progress"] == 1
