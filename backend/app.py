from __future__ import annotations

import os
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Tuple

from flask import (
    Flask,
    Response,
    g,
    jsonify,
    request,
    send_from_directory,
    session,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from .database import Base, SessionLocal, engine
from .models import Activity, Client, Employee, Month, Project, Task, TaskActivity, Team
from .seed import seed


def create_app() -> Flask:
    frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    static_folder = str(frontend_dist) if frontend_dist.exists() else None

    app = Flask(__name__, static_folder=static_folder, static_url_path="/")
    app.secret_key = os.getenv("SECRET_KEY", "creagy-dev-secret")

    Base.metadata.create_all(engine)
    seed()

    @app.before_request
    def before_request() -> Response | None:
        if request.method == "OPTIONS":
            response = app.make_default_options_response()
            response.status_code = 204
            return response
        g.db = SessionLocal()
        return None

    @app.after_request
    def apply_cors(response: Response) -> Response:
        allowed_origins = {
            origin.strip()
            for origin in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
            if origin.strip()
        }
        origin = request.headers.get("Origin")
        if origin and (not allowed_origins or origin in allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif not origin:
            response.headers["Access-Control-Allow-Origin"] = request.host_url.rstrip("/")
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
        return response

    @app.teardown_request
    def teardown_request(exception: Exception | None) -> None:
        db = getattr(g, "db", None)
        if db is not None:
            if exception:
                db.rollback()
            db.close()
        SessionLocal.remove()

    def current_user() -> Employee | None:
        employee_id = session.get("employee_id")
        if not employee_id:
            return None
        return g.db.get(Employee, employee_id)

    def require_user() -> Employee:
        user = current_user()
        if not user:
            raise Unauthorized("Authentication required.")
        return user

    class Unauthorized(Exception):
        def __init__(self, message: str) -> None:
            self.message = message

    class BadRequest(Exception):
        def __init__(self, message: str) -> None:
            self.message = message

    @app.errorhandler(Unauthorized)
    def handle_unauthorized(error: Unauthorized):  # type: ignore[override]
        return jsonify({"error": error.message}), 401

    @app.errorhandler(BadRequest)
    def handle_bad_request(error: BadRequest):  # type: ignore[override]
        return jsonify({"error": error.message}), 400

    @app.route("/api/ping", methods=["GET"])
    def ping():
        return jsonify({"status": "ok"})

    @app.route("/api/session", methods=["GET"])
    def get_session():
        user = current_user()
        if not user:
            return jsonify({"user": None})
        return jsonify({"user": serialize_employee(user)})

    @app.route("/api/session", methods=["POST"])
    def create_session():
        payload = request.get_json(force=True, silent=True) or {}
        employee_id = payload.get("employeeId")
        if not employee_id:
            raise BadRequest("employeeId is required.")
        employee = g.db.get(Employee, int(employee_id))
        if not employee:
            raise BadRequest("Employee not found.")
        session["employee_id"] = employee.id
        return jsonify({"user": serialize_employee(employee)})

    @app.route("/api/session", methods=["DELETE"])
    def delete_session():
        session.clear()
        return jsonify({"success": True})

    @app.route("/api/employees", methods=["GET"])
    def list_employees():
        employees = g.db.scalars(select(Employee).order_by(Employee.name)).all()
        return jsonify({"employees": [serialize_employee(emp) for emp in employees]})

    @app.route("/api/employees", methods=["POST"])
    def create_employee():
        payload = request.get_json(force=True, silent=True) or {}
        name = (payload.get("name") or "").strip()
        team_id = payload.get("teamId")
        if not name:
            raise BadRequest("Employee name is required.")
        team = g.db.get(Team, int(team_id)) if team_id else None
        try:
            employee = Employee(name=name, team=team)
            g.db.add(employee)
            g.db.commit()
        except IntegrityError:
            g.db.rollback()
            employee = g.db.scalar(select(Employee).where(Employee.name == name))
            if not employee:
                raise BadRequest("Unable to create employee.")
        session["employee_id"] = employee.id
        return jsonify({"user": serialize_employee(employee)})

    @app.route("/api/teams", methods=["GET"])
    def list_teams():
        teams = g.db.scalars(select(Team).order_by(Team.name)).all()
        return jsonify({"teams": [serialize_team(team) for team in teams]})

    @app.route("/api/clients", methods=["GET"])
    def list_clients():
        clients = g.db.scalars(select(Client).order_by(Client.name)).all()
        return jsonify({"clients": [serialize_client(client) for client in clients]})

    @app.route("/api/activities", methods=["GET"])
    def list_activities():
        activities = g.db.scalars(select(Activity).order_by(Activity.type)).all()
        return jsonify({"activities": [serialize_activity(activity) for activity in activities]})

    @app.route("/api/months", methods=["GET"])
    def list_months():
        months = g.db.scalars(select(Month).order_by(Month.yyyy_mm)).all()
        return jsonify({"months": [serialize_month(month) for month in months]})

    @app.route("/api/projects", methods=["GET"])
    def list_projects():
        user = current_user()
        projects = (
            g.db.execute(
                select(Project)
                .options(
                    selectinload(Project.project_manager),
                    selectinload(Project.client),
                    selectinload(Project.team),
                    selectinload(Project.created_by),
                )
                .order_by(Project.start_date)
            )
            .scalars()
            .all()
        )
        return jsonify(
            {
                "projects": [
                    serialize_project_summary(project, user_id=user.id if user else None)
                    for project in projects
                ]
            }
        )

    @app.route("/api/projects", methods=["POST"])
    def create_project():
        user = require_user()
        payload = request.get_json(force=True, silent=True) or {}
        name = (payload.get("name") or "").strip()
        manager_id = payload.get("projectManagerId")
        client_id = payload.get("clientId")
        client_name = (payload.get("clientName") or "").strip()
        team_id = payload.get("teamId")
        budget = Decimal(str(payload.get("budget", "0") or "0"))
        start_date_str = payload.get("startDate")
        end_date_str = payload.get("endDate")

        if not all([name, manager_id, team_id, start_date_str, end_date_str]):
            raise BadRequest("Missing required project fields.")

        project_manager = g.db.get(Employee, int(manager_id))
        if not project_manager:
            raise BadRequest("Project manager not found.")

        client = g.db.get(Client, int(client_id)) if client_id else None
        if not client and client_name:
            client = Client(name=client_name)
            g.db.add(client)
            g.db.flush()
        if not client:
            raise BadRequest("Client selection is required.")

        team = g.db.get(Team, int(team_id))
        if not team:
            raise BadRequest("Team not found.")

        try:
            start_date_value = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date_value = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise BadRequest("Invalid date format. Use YYYY-MM-DD.")
        if end_date_value < start_date_value:
            raise BadRequest("End date must be on or after start date.")

        project = Project(
            name=name,
            project_manager=project_manager,
            client=client,
            team=team,
            budget=budget,
            start_date=start_date_value,
            end_date=end_date_value,
            created_by=user,
        )
        g.db.add(project)
        try:
            g.db.commit()
        except IntegrityError:
            g.db.rollback()
            raise BadRequest("A project with that name already exists.")
        return jsonify({"project": serialize_project(project, include_tasks=False)})

    @app.route("/api/projects/<int:project_id>", methods=["GET"])
    def get_project(project_id: int):
        user = current_user()
        project = (
            g.db.execute(
                select(Project)
                .where(Project.id == project_id)
                .options(
                    selectinload(Project.project_manager),
                    selectinload(Project.client),
                    selectinload(Project.team),
                    selectinload(Project.created_by),
                    selectinload(Project.tasks)
                    .selectinload(Task.assignee),
                    selectinload(Project.tasks)
                    .selectinload(Task.task_activities)
                    .selectinload(TaskActivity.month),
                    selectinload(Project.tasks)
                    .selectinload(Task.task_activities)
                    .selectinload(TaskActivity.activity),
                )
            )
            .scalars()
            .first()
        )
        if not project:
            raise BadRequest("Project not found.")

        task_map: Dict[int, List[TaskActivity]] = {
            task.id: list(task.task_activities)
            for task in project.tasks
        }
        detail = {
            "project": serialize_project(project, include_tasks=True),
            "ganttData": build_gantt_data(project, task_map),
            "mandayChart": build_manday_chart(project, task_map),
            "summary": build_summary_stats(project),
            "canManageTasks": bool(user and user.id == project.project_manager_id),
        }
        return jsonify(detail)

    @app.route("/api/projects/<int:project_id>/tasks", methods=["POST"])
    def create_task(project_id: int):
        user = require_user()
        project = g.db.get(Project, project_id)
        if not project:
            raise BadRequest("Project not found.")
        if project.project_manager_id != user.id:
            raise Unauthorized("Only the project manager can add tasks.")

        payload = request.get_json(force=True, silent=True) or {}
        name = (payload.get("name") or "").strip()
        assignee_id = payload.get("assigneeId")
        manday = Decimal(str(payload.get("manday", "0") or "0"))
        budget = Decimal(str(payload.get("budget", "0") or "0"))
        status = (payload.get("status") or "Planned").strip() or "Planned"
        activities_payload = payload.get("activities") or []

        if not name or not assignee_id:
            raise BadRequest("Task name and assignee are required.")

        assignee = g.db.get(Employee, int(assignee_id))
        if not assignee:
            raise BadRequest("Assignee not found.")

        task = Task(
            name=name,
            project=project,
            assignee=assignee,
            manday=manday,
            budget=budget,
            status=status,
        )
        g.db.add(task)
        g.db.flush()

        seen_pairs: set[Tuple[int, int]] = set()
        for entry in activities_payload:
            month_id = entry.get("monthId")
            activity_id = entry.get("activityId")
            if not month_id or not activity_id:
                continue
            pair = (int(month_id), int(activity_id))
            if pair in seen_pairs:
                continue
            month = g.db.get(Month, pair[0])
            activity = g.db.get(Activity, pair[1])
            if not month or not activity:
                continue
            g.db.add(TaskActivity(task=task, month=month, activity=activity))
            seen_pairs.add(pair)

        if not seen_pairs:
            g.db.rollback()
            raise BadRequest("At least one month/activity pair is required.")

        try:
            g.db.commit()
        except IntegrityError:
            g.db.rollback()
            raise BadRequest("A task with that name already exists for this project.")

        task = (
            g.db.execute(
                select(Task)
                .where(Task.id == task.id)
                .options(
                    selectinload(Task.assignee),
                    selectinload(Task.task_activities)
                    .selectinload(TaskActivity.month),
                    selectinload(Task.task_activities)
                    .selectinload(TaskActivity.activity),
                )
            )
            .scalars()
            .first()
        )
        return jsonify({"task": serialize_task(task)})

    if static_folder:
        @app.route("/", defaults={"path": ""})
        @app.route("/<path:path>")
        def serve_frontend(path: str):
            target = Path(static_folder) / path
            if path and target.exists() and target.is_file():
                return send_from_directory(static_folder, path)
            return send_from_directory(static_folder, "index.html")

    return app


def serialize_employee(employee: Employee) -> Dict[str, Any]:
    return {
        "id": employee.id,
        "name": employee.name,
        "team": serialize_team(employee.team) if employee.team else None,
    }


def serialize_team(team: Team) -> Dict[str, Any]:
    return {"id": team.id, "name": team.name}


def serialize_client(client: Client) -> Dict[str, Any]:
    return {"id": client.id, "name": client.name}


def serialize_activity(activity: Activity) -> Dict[str, Any]:
    return {"id": activity.id, "type": activity.type}


def serialize_month(month: Month) -> Dict[str, Any]:
    return {"id": month.id, "label": month.yyyy_mm}


def serialize_task(task: Task | None) -> Dict[str, Any]:
    if not task:
        return {}
    return {
        "id": task.id,
        "name": task.name,
        "manday": float(task.manday or 0),
        "budget": float(task.budget or 0),
        "status": task.status,
        "assignee": serialize_employee(task.assignee) if task.assignee else None,
        "activities": [
            {
                "month": serialize_month(activity.month),
                "activity": serialize_activity(activity.activity),
            }
            for activity in sorted(
                task.task_activities,
                key=lambda ta: ta.month.yyyy_mm if ta.month else "",
            )
        ],
    }


def serialize_project(project: Project, include_tasks: bool = False) -> Dict[str, Any]:
    payload = {
        "id": project.id,
        "name": project.name,
        "budget": float(project.budget or 0),
        "status": project.status,
        "startDate": project.start_date.isoformat(),
        "endDate": project.end_date.isoformat(),
        "projectManager": serialize_employee(project.project_manager) if project.project_manager else None,
        "client": serialize_client(project.client) if project.client else None,
        "team": serialize_team(project.team) if project.team else None,
        "createdBy": serialize_employee(project.created_by) if project.created_by else None,
    }
    if include_tasks:
        payload["tasks"] = [serialize_task(task) for task in project.tasks]
    return payload


def serialize_project_summary(project: Project, user_id: int | None = None) -> Dict[str, Any]:
    summary = serialize_project(project, include_tasks=False)
    summary["isProjectManager"] = user_id == project.project_manager_id if user_id else False
    return summary


def build_gantt_data(project: Project, task_map: Dict[int, List[TaskActivity]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = [
        {
            "id": f"project-{project.id}",
            "name": project.name,
            "start": project.start_date.isoformat(),
            "end": project.end_date.isoformat(),
            "progress": 0,
            "customClass": "gantt-project",
        }
    ]
    for task in project.tasks:
        activities = task_map.get(task.id, [])
        if not activities:
            continue
        start_date, end_date = compute_task_window(activities)
        data.append(
            {
                "id": f"task-{task.id}",
                "name": task.name,
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "progress": 0,
                "dependencies": f"project-{project.id}",
                "customClass": "gantt-task",
            }
        )
    return data


def build_manday_chart(project: Project, task_map: Dict[int, List[TaskActivity]]) -> Dict[str, Any]:
    month_totals: Dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for task in project.tasks:
        activities = task_map.get(task.id, [])
        if not activities:
            continue
        months = sorted({activity.month.yyyy_mm for activity in activities if activity.month})
        if not months:
            continue
        share = (task.manday or Decimal("0")) / Decimal(len(months))
        for month_label in months:
            month_totals[month_label] += share

    labels = sorted(month_totals.keys())
    values = [float(round(month_totals[label], 2)) for label in labels]
    return {"labels": labels, "values": values}


def build_summary_stats(project: Project) -> Dict[str, Any]:
    duration_months = month_difference(project.start_date, project.end_date) + 1
    total_manday = sum(float(task.manday or 0) for task in project.tasks)
    total_budget = float(project.budget or 0) + sum(float(task.budget or 0) for task in project.tasks)
    return {
        "durationMonths": duration_months,
        "totalManday": round(total_manday, 2),
        "totalBudget": round(total_budget, 2),
    }


def compute_task_window(activities: List[TaskActivity]) -> Tuple[date, date]:
    months = [activity.month.yyyy_mm for activity in activities if activity.month]
    parsed_dates = [parse_month_label(label) for label in months]
    start = min(parsed_dates)
    end = max(parsed_dates)
    end_year, end_month = end.year, end.month
    if end_month == 12:
        final_date = date(end_year, 12, 31)
    else:
        final_date = date(end_year, end_month + 1, 1) - date.resolution
    return start, final_date


def parse_month_label(label: str) -> date:
    return datetime.strptime(f"{label}-01", "%Y-%m-%d").date()


def month_difference(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month)


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
