from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from .database import Base, engine, session_scope
from .models import Activity, Client, Employee, Month, Team


EMPLOYEES = [
    "Sitthichat",
    "Boonrod",
    "Phatchariya",
    "Jiraporn",
    "Panwad",
    "Kittinut",
    "Bunyanuch",
    "Sairung",
    "Wasintara",
    "Warisara",
    "Vaivisarn",
    "Tharaya",
    "Prangvalai",
    "Pohnnappan",
    "Kornkanok",
    "Ray",
    "Wararat",
    "Chonthicha",
]

TEAMS = [
    "Corporate Advisory",
    "Public Advisory: Mitigation",
    "Public Advisory: Adaptation",
]

ACTIVITY_TYPES = [
    "Workday",
    "Meeting",
    "Focus group",
    "Workshop",
    "Site visit",
    "Deliverable",
]


def ensure_instance_dir() -> None:
    Path(__file__).resolve().parent.parent.joinpath("instance").mkdir(exist_ok=True)


def seed() -> None:
    ensure_instance_dir()
    Base.metadata.create_all(engine)

    with session_scope() as session:
        # Seed teams
        for team_name in TEAMS:
            if not session.scalar(select(Team).where(Team.name == team_name)):
                session.add(Team(name=team_name))

        session.flush()

        team_rows = session.scalars(select(Team)).all()
        team_cycle = list(team_rows) or [None]

        # Seed employees and assign teams in round robin
        for idx, employee_name in enumerate(EMPLOYEES):
            if not session.scalar(select(Employee).where(Employee.name == employee_name)):
                team = team_cycle[idx % len(team_cycle)] if team_cycle else None
                session.add(Employee(name=employee_name, team=team))

        # Seed clients placeholder for initial selection
        if not session.scalar(select(Client).limit(1)):
            session.add(Client(name="Demo Client"))

        # Seed months between June 2025 and December 2026 inclusive
        start_year, start_month = 2025, 6
        end_year, end_month = 2026, 12

        current_year, current_month = start_year, start_month
        while (current_year, current_month) <= (end_year, end_month):
            label = f"{current_year:04d}-{current_month:02d}"
            if not session.scalar(select(Month).where(Month.yyyy_mm == label)):
                session.add(Month(yyyy_mm=label))
            if current_month == 12:
                current_month = 1
                current_year += 1
            else:
                current_month += 1

        # Seed activity types
        for activity_type in ACTIVITY_TYPES:
            if not session.scalar(select(Activity).where(Activity.type == activity_type)):
                session.add(Activity(type=activity_type))


if __name__ == "__main__":
    seed()
    print("Database seeded.")
