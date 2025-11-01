from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from .database import SessionLocal, engine
from .models import Base, Project, ProjectStatus, Task, TaskStatus

DATA_PATH = Path(__file__).resolve().parent / "data" / "sample_data.json"


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def load_seed_data() -> dict[str, list[dict[str, object]]]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Sample data file not found: {DATA_PATH}")
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def reset_database(session: Session) -> None:
    session.execute(delete(Task))
    session.execute(delete(Project))
    session.flush()


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    payload = load_seed_data()

    with SessionLocal() as session:
        reset_database(session)

        for project_payload in payload.get("projects", []):
            project = Project(
                id=int(project_payload["id"]),
                name=str(project_payload["name"]),
                client=str(project_payload["client"]),
                project_manager=str(project_payload["project_manager"]),
                budget=Decimal(str(project_payload["budget"])),
                start_date=parse_date(str(project_payload["start_date"])),
                end_date=parse_date(project_payload.get("end_date")),
                status=ProjectStatus(project_payload["status"]),
            )
            session.add(project)

        session.flush()

        for task_payload in payload.get("tasks", []):
            task = Task(
                id=int(task_payload["id"]),
                project_id=int(task_payload["project_id"]),
                name=str(task_payload["name"]),
                assignee=str(task_payload["assignee"]),
                man_days=float(task_payload["man_days"]),
                start_date=parse_date(str(task_payload["start_date"])),
                end_date=parse_date(task_payload.get("end_date")),
                status=TaskStatus(task_payload["status"]),
                progress=float(task_payload.get("progress", 0.0)),
                remarks=task_payload.get("remarks"),
            )
            session.add(task)

        session.commit()

        print(
            f"Seeded {len(payload.get('projects', []))} projects and "
            f"{len(payload.get('tasks', []))} tasks for demo environment."
        )


if __name__ == "__main__":
    seed()
