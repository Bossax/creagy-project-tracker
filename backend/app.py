from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

from .database import SessionLocal, Base, engine
from .models import Activity, Client, Employee, Month, Project, Task, TaskActivity, Team
from .seed import seed


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = os.getenv("SECRET_KEY", "creagy-dev-secret")

    # Ensure database exists
    Base.metadata.create_all(engine)
    seed()

    @app.before_request
    def before_request() -> None:
        g.db = SessionLocal()

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

    def require_login() -> Employee:
        user = current_user()
        if not user:
            flash("Please choose your employee profile to continue.", "warning")
            raise Redirect(url_for("index"))
        return user

    class Redirect(Exception):
        def __init__(self, location: str) -> None:
            self.location = location

    @app.errorhandler(Redirect)
    def handle_redirect(error: Redirect):  # type: ignore[override]
        return redirect(error.location)

    @app.route("/", methods=["GET"])
    def index():
        employees = g.db.scalars(select(Employee).order_by(Employee.name)).all()
        teams = g.db.scalars(select(Team).order_by(Team.name)).all()
        return render_template("index.html", employees=employees, teams=teams, user=current_user())

    @app.route("/login", methods=["POST"])
    def login():
        employee_id = request.form.get("employee_id")
        if not employee_id:
            flash("Please select an employee.", "danger")
            return redirect(url_for("index"))

        employee = g.db.get(Employee, int(employee_id))
        if not employee:
            flash("Employee not found.", "danger")
            return redirect(url_for("index"))

        session["employee_id"] = employee.id
        flash(f"Welcome back, {employee.name}!", "success")
        return redirect(url_for("dashboard"))

    @app.route("/employees", methods=["POST"])
    def create_employee():
        name = request.form.get("name", "").strip()
        team_id = request.form.get("team_id")
        if not name:
            flash("Employee name is required.", "danger")
            return redirect(url_for("index"))

        team = g.db.get(Team, int(team_id)) if team_id else None
        try:
            employee = Employee(name=name, team=team)
            g.db.add(employee)
            g.db.commit()
        except IntegrityError:
            g.db.rollback()
            employee = g.db.scalar(select(Employee).where(Employee.name == name))

        session["employee_id"] = employee.id
        flash(f"Welcome, {employee.name}! Your profile has been created.", "success")
        return redirect(url_for("dashboard"))

    @app.route("/logout")
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/dashboard")
    def dashboard():
        try:
            user = require_login()
        except Redirect as redirect_exc:
            return redirect(redirect_exc.location)

        projects = (
            g.db.execute(
                select(Project)
                .options(selectinload(Project.project_manager), selectinload(Project.client))
                .order_by(Project.start_date)
            )
            .scalars()
            .all()
        )
        return render_template("dashboard.html", user=user, projects=projects)

    @app.route("/projects/new", methods=["GET", "POST"])
    def new_project():
        try:
            user = require_login()
        except Redirect as redirect_exc:
            return redirect(redirect_exc.location)

        employees = g.db.scalars(select(Employee).order_by(Employee.name)).all()
        clients = g.db.scalars(select(Client).order_by(Client.name)).all()
        teams = g.db.scalars(select(Team).order_by(Team.name)).all()

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            project_manager_id = request.form.get("project_manager_id")
            client_id = request.form.get("client_id")
            new_client_name = request.form.get("new_client_name", "").strip()
            team_id = request.form.get("team_id")
            budget = request.form.get("budget", "0")
            start_date_str = request.form.get("start_date")
            end_date_str = request.form.get("end_date")

            if not name or not project_manager_id or not team_id or not start_date_str or not end_date_str:
                flash("Please complete all required fields.", "danger")
                return render_template(
                    "new_project.html",
                    user=user,
                    employees=employees,
                    clients=clients,
                    teams=teams,
                )

            project_manager = g.db.get(Employee, int(project_manager_id))
            if not project_manager:
                flash("Selected project manager not found.", "danger")
                return render_template(
                    "new_project.html",
                    user=user,
                    employees=employees,
                    clients=clients,
                    teams=teams,
                )

            client = None
            if client_id:
                client = g.db.get(Client, int(client_id))
            if not client and new_client_name:
                client = Client(name=new_client_name)
                g.db.add(client)
                g.db.flush()

            if not client:
                flash("Please select an existing client or enter a new client name.", "danger")
                return render_template(
                    "new_project.html",
                    user=user,
                    employees=employees,
                    clients=clients,
                    teams=teams,
                )

            try:
                parsed_budget = Decimal(budget)
            except Exception:
                flash("Budget must be a number.", "danger")
                return render_template(
                    "new_project.html",
                    user=user,
                    employees=employees,
                    clients=clients,
                    teams=teams,
                )

            try:
                start_date_value = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date_value = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Dates must be in YYYY-MM-DD format.", "danger")
                return render_template(
                    "new_project.html",
                    user=user,
                    employees=employees,
                    clients=clients,
                    teams=teams,
                )

            if end_date_value < start_date_value:
                flash("End date must be on or after start date.", "danger")
                return render_template(
                    "new_project.html",
                    user=user,
                    employees=employees,
                    clients=clients,
                    teams=teams,
                )

            project = Project(
                name=name,
                project_manager=project_manager,
                client=client,
                team=g.db.get(Team, int(team_id)),
                budget=parsed_budget,
                start_date=start_date_value,
                end_date=end_date_value,
                created_by=user,
            )
            g.db.add(project)
            try:
                g.db.commit()
                flash("Project created successfully.", "success")
                return redirect(url_for("project_detail", project_id=project.id))
            except IntegrityError:
                g.db.rollback()
                flash("A project with that name already exists.", "danger")

        return render_template(
            "new_project.html",
            user=user,
            employees=employees,
            clients=clients,
            teams=teams,
        )

    @app.route("/projects/<int:project_id>")
    def project_detail(project_id: int):
        try:
            user = require_login()
        except Redirect as redirect_exc:
            return redirect(redirect_exc.location)

        project = g.db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.project_manager),
                selectinload(Project.client),
                selectinload(Project.tasks)
                .selectinload(Task.assignee),
            )
        ).scalar_one_or_none()

        if not project:
            flash("Project not found.", "danger")
            return redirect(url_for("dashboard"))

        months = g.db.scalars(select(Month).order_by(Month.yyyy_mm)).all()
        activities = g.db.scalars(select(Activity).order_by(Activity.type)).all()
        employees = g.db.scalars(select(Employee).order_by(Employee.name)).all()

        task_map = {
            task.id: g.db.execute(
                select(TaskActivity)
                .where(TaskActivity.task_id == task.id)
                .options(
                    selectinload(TaskActivity.month),
                    selectinload(TaskActivity.activity),
                )
            )
            .scalars()
            .all()
            for task in project.tasks
        }

        gantt_data = build_gantt_data(project, task_map)
        manday_chart = build_manday_chart(project, task_map)
        summary_stats = build_summary_stats(project)

        return render_template(
            "project_detail.html",
            user=user,
            project=project,
            months=months,
            activities=activities,
            employees=employees,
            task_map=task_map,
            gantt_data=json.dumps(gantt_data),
            manday_chart=json.dumps(manday_chart),
            summary_stats=summary_stats,
            can_manage_tasks=user.id == project.project_manager_id,
        )

    @app.route("/projects/<int:project_id>/tasks/new", methods=["POST"])
    def create_task(project_id: int):
        try:
            user = require_login()
        except Redirect as redirect_exc:
            return redirect(redirect_exc.location)

        project = g.db.get(Project, project_id)
        if not project:
            flash("Project not found.", "danger")
            return redirect(url_for("dashboard"))

        if project.project_manager_id != user.id:
            flash("Only the project manager can add tasks.", "danger")
            return redirect(url_for("project_detail", project_id=project.id))

        name = request.form.get("task_name", "").strip()
        assignee_id = request.form.get("assignee_id")
        manday = request.form.get("manday", "0")
        budget = request.form.get("budget", "0")
        status = request.form.get("status", "Planned")
        month_ids = request.form.getlist("month_ids[]")
        activity_ids = request.form.getlist("activity_ids[]")

        if not name or not assignee_id:
            flash("Task name and assignee are required.", "danger")
            return redirect(url_for("project_detail", project_id=project.id))

        try:
            manday_value = Decimal(manday)
            budget_value = Decimal(budget)
        except Exception:
            flash("Manday and budget must be numeric.", "danger")
            return redirect(url_for("project_detail", project_id=project.id))

        assignee = g.db.get(Employee, int(assignee_id))
        if not assignee:
            flash("Selected assignee not found.", "danger")
            return redirect(url_for("project_detail", project_id=project.id))

        task = Task(
            name=name,
            project=project,
            assignee=assignee,
            manday=manday_value,
            budget=budget_value,
            status=status,
        )
        g.db.add(task)
        g.db.flush()

        pairs = list(zip(month_ids, activity_ids))
        added_pairs: set[Tuple[int, int]] = set()
        for month_id_str, activity_id_str in pairs:
            if not month_id_str or not activity_id_str:
                continue
            pair = (int(month_id_str), int(activity_id_str))
            if pair in added_pairs:
                continue
            month = g.db.get(Month, pair[0])
            activity = g.db.get(Activity, pair[1])
            if not month or not activity:
                continue
            g.db.add(TaskActivity(task=task, month=month, activity=activity))
            added_pairs.add(pair)

        if not added_pairs:
            flash("Please assign at least one month and activity to the task.", "danger")
            g.db.rollback()
            return redirect(url_for("project_detail", project_id=project.id))

        try:
            g.db.commit()
            flash("Task created successfully.", "success")
        except IntegrityError:
            g.db.rollback()
            flash("A task with that name already exists for this project.", "danger")

        return redirect(url_for("project_detail", project_id=project.id))

    return app


def build_gantt_data(project: Project, task_map: Dict[int, List[TaskActivity]]) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    data.append(
        {
            "id": f"project-{project.id}",
            "name": project.name,
            "start": project.start_date.isoformat(),
            "end": project.end_date.isoformat(),
            "progress": 0,
            "custom_class": "gantt-project",
        }
    )
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
                "custom_class": "gantt-task",
            }
        )
    return data


def build_manday_chart(project: Project, task_map: Dict[int, List[TaskActivity]]) -> Dict[str, Any]:
    month_totals: Dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    for task in project.tasks:
        activities = task_map.get(task.id, [])
        if not activities:
            continue
        months = sorted({activity.month.yyyy_mm for activity in activities})
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
        "duration_months": duration_months,
        "total_manday": round(total_manday, 2),
        "total_budget": round(total_budget, 2),
    }


def compute_task_window(activities: List[TaskActivity]) -> Tuple[date, date]:
    months = [activity.month.yyyy_mm for activity in activities]
    parsed_dates = [parse_month_label(label) for label in months]
    start = min(parsed_dates)
    end = max(parsed_dates)
    end_year, end_month = end.year, end.month
    # Move to last day of the end month
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
