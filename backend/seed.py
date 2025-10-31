"""Database seeding utilities for the Creagy project tracker."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import delete

from .database import Base, engine, session_scope
from .models import Project, Task

PROJECT_DATA_FILENAME = "sample_projects.json"
DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DATA_PATH = DATA_DIRECTORY / PROJECT_DATA_FILENAME


def parse_date(value: str | None) -> date | None:
    """Parse ISO formatted date strings into :class:`datetime.date`."""
    if not value:
        return None
    return date.fromisoformat(value)


def load_seed_data(path: Path) -> list[dict[str, Any]]:
    """Load structured seed data from a JSON file."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def initialise_schema(drop_existing: bool = False) -> None:
    """Create database schema, optionally dropping existing tables first."""
    if drop_existing:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def clear_existing_data() -> None:
    """Remove existing project and task records prior to seeding."""
    with session_scope() as session:
        session.execute(delete(Task))
        session.execute(delete(Project))


def seed_database(records: Iterable[dict[str, Any]]) -> None:
    """Populate the database with the provided project and task records."""
    with session_scope() as session:
        for project_data in records:
            tasks_data = project_data.get("tasks", [])

            project = Project(
                name=project_data.get("name"),
                owner=project_data.get("owner"),
                status=project_data.get("status"),
                start_date=parse_date(project_data.get("start_date")),
                end_date=parse_date(project_data.get("end_date")),
                notes=project_data.get("notes"),
            )
            session.add(project)
            session.flush()  # Ensure ``project.id`` is available for tasks.

            for task_data in tasks_data:
                task = Task(
                    project_id=project.id,
                    name=task_data.get("name"),
                    owner=task_data.get("owner"),
                    status=task_data.get("status"),
                    due_date=parse_date(task_data.get("due_date")),
                    notes=task_data.get("notes"),
                )
                session.add(task)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the seeding script."""
    parser = argparse.ArgumentParser(description="Seed the project tracker database")
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help=f"Path to a JSON file containing project/task data (default: {DEFAULT_DATA_PATH})",
    )
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop existing tables before recreating them.",
    )
    parser.add_argument(
        "--skip-clear",
        action="store_true",
        help="Do not clear existing project/task records before inserting seed data.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for the seeding script."""
    args = parse_args()
    data_file = args.data

    if not data_file.exists():
        raise FileNotFoundError(f"Seed data file not found: {data_file}")

    records = load_seed_data(data_file)
    if not isinstance(records, list):
        raise ValueError("Seed data must be a list of project dictionaries")

    initialise_schema(drop_existing=args.drop)

    if not args.skip_clear:
        clear_existing_data()

    seed_database(records)

    print(
        "Seeded database with",
        len(records),
        "projects from",
        data_file,
    )


if __name__ == "__main__":
    main()
