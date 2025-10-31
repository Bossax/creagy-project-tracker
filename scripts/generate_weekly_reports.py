"""Generate weekly project summaries for Creagy project tracker."""
from __future__ import annotations

import argparse
import csv
from contextlib import contextmanager
from datetime import datetime
import json
import sys
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:  # pragma: no cover - compatible with lightweight SQLAlchemy stub
    from sqlalchemy.exc import OperationalError
except ModuleNotFoundError:  # pragma: no cover - fallback for stubbed environments
    class OperationalError(RuntimeError):
        """Fallback error used when SQLAlchemy is unavailable."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

from backend.database import (  # noqa: E402  pylint: disable=wrong-import-position
    SessionLocal,
)
from scripts.utils import (  # noqa: E402  pylint: disable=wrong-import-position
    ProjectRecord,
    TaskRecord,
    fetch_projects_from_db,
    load_projects_from_export,
    summarise_project,
)


@contextmanager
def _session_from_factory():
    """Provide a session that gracefully handles stubbed environments."""

    session = SessionLocal()
    try:
        yield session
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()


def _ensure_parent_directory(path: Path) -> None:
    """Create parent directories for ``path`` if required."""

    path.parent.mkdir(parents=True, exist_ok=True)


def _format_upcoming_tasks(tasks: Iterable[TaskRecord]) -> str:
    """Return a human readable description for upcoming tasks."""

    parts: list[str] = []
    for task in tasks:
        due = task.due_date.isoformat() if task.due_date else "—"
        owner = task.owner or "Unassigned"
        status = task.status or "Unknown"
        parts.append(f"{due} · {task.name} ({owner}, {status})")
    return "; ".join(parts)


def _markdown_for_project(summary: dict[str, object]) -> str:
    """Return markdown snippet for a single project."""

    budget = summary["budget"]
    upcoming = summary["upcoming_tasks"]
    breakdown = summary["status_breakdown"].items()

    lines = [
        f"## {summary['project_name']}",
        "",
        f"**Owner:** {summary.get('owner') or 'Unassigned'}",
        f"**Status:** {summary.get('status') or 'Unknown'}",
        f"**Completion:** {summary['completion_percentage']}%",
        "",
        "### Status breakdown",
    ]
    if breakdown:
        lines.append("| Status | Tasks |")
        lines.append("| --- | ---: |")
        for status, count in breakdown:
            lines.append(f"| {status or 'Unknown'} | {count} |")
    else:
        lines.append("No tasks recorded for this project yet.")

    lines.extend(
        (
            "",
            "### Budget",
            f"Allocated: ${budget['allocated']:,.0f}",
            f"Spent: ${budget['spent']:,.0f}",
            f"Remaining: ${budget['remaining']:,.0f}",
        )
    )

    if upcoming:
        lines.append("")
        lines.append("### Upcoming tasks")
        lines.append("| Due | Task | Owner | Status |")
        lines.append("| --- | --- | --- | --- |")
        for task in upcoming:
            due = task.due_date.isoformat() if task.due_date else "—"
            lines.append(
                f"| {due} | {task.name} | {task.owner or 'Unassigned'} | {task.status or 'Unknown'} |"
            )

    notes = summary.get("notes")
    if notes:
        lines.extend(("", "### Notes", notes))

    lines.append("")
    return "\n".join(lines)


def _email_digest_line(summary: dict[str, object]) -> str:
    """Return a concise, email friendly summary for a project."""

    breakdown = summary["status_breakdown"]
    status_parts = ", ".join(
        f"{status or 'Unknown'}: {count}" for status, count in breakdown.items()
    )
    upcoming = summary["upcoming_tasks"]
    upcoming_text = _format_upcoming_tasks(upcoming)
    budget = summary["budget"]

    components = [
        f"{summary['project_name']} — {summary['completion_percentage']}% complete",
        f"Status: {summary.get('status') or 'Unknown'}",
    ]
    if status_parts:
        components.append(f"Breakdown [{status_parts}]")
    if upcoming_text:
        components.append(f"Upcoming: {upcoming_text}")
    components.append(
        f"Budget ${budget['spent']:,.0f} spent / ${budget['allocated']:,.0f} allocated"
    )
    return "; ".join(components)


def _write_markdown(path: Path, summaries: list[dict[str, object]]) -> None:
    """Write the weekly summary in Markdown format."""

    _ensure_parent_directory(path)
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    content_lines = [f"# Weekly portfolio update", "", f"Generated {generated_at}", ""]
    for summary in summaries:
        content_lines.append(_markdown_for_project(summary))
    content = "\n".join(content_lines)
    path.write_text(content, encoding="utf-8")


def _write_csv(path: Path, summaries: list[dict[str, object]]) -> None:
    """Persist key metrics to a CSV file for spreadsheet tooling."""

    _ensure_parent_directory(path)
    fieldnames = [
        "project_id",
        "project_name",
        "owner",
        "status",
        "completion_percentage",
        "total_tasks",
        "completed_tasks",
        "in_progress_tasks",
        "not_started_tasks",
        "budget_allocated",
        "budget_spent",
        "budget_remaining",
        "upcoming_tasks",
        "notes",
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries:
            breakdown = summary["status_breakdown"]
            writer.writerow(
                {
                    "project_id": summary.get("project_id"),
                    "project_name": summary["project_name"],
                    "owner": summary.get("owner"),
                    "status": summary.get("status"),
                    "completion_percentage": summary["completion_percentage"],
                    "total_tasks": summary["total_tasks"],
                    "completed_tasks": breakdown.get("Completed", 0),
                    "in_progress_tasks": breakdown.get("In Progress", 0),
                    "not_started_tasks": breakdown.get("Not Started", 0),
                    "budget_allocated": summary["budget"]["allocated"],
                    "budget_spent": summary["budget"]["spent"],
                    "budget_remaining": summary["budget"]["remaining"],
                    "upcoming_tasks": _format_upcoming_tasks(summary["upcoming_tasks"]),
                    "notes": summary.get("notes", ""),
                }
            )


def _write_email(path: Path, summaries: list[dict[str, object]]) -> None:
    """Write a plaintext digest suitable for email distribution."""

    _ensure_parent_directory(path)
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"Weekly portfolio update — generated {generated_at}", ""]
    for summary in summaries:
        lines.append(_email_digest_line(summary))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_projects_from_source(args: argparse.Namespace) -> list[ProjectRecord]:
    """Return projects using the selected data source."""

    if args.source == "export":
        if not args.export_path:
            msg = "--export-path is required when --source export"
            raise SystemExit(msg)
        return load_projects_from_export(args.export_path)

    with _session_from_factory() as session:
        try:
            return fetch_projects_from_db(session)
        except OperationalError as exc:
            msg = (
                "Database query failed. Ensure migrations have been applied "
                "(e.g. `alembic upgrade head`) or create the SQLite schema "
                "with `python -m backend.database`."
            )
            raise SystemExit(f"{msg}\nOriginal error: {exc}") from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments for the CLI script."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/weekly.md"),
        help="Path to the Markdown report to create.",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Optional path to export portfolio metrics as CSV.",
    )
    parser.add_argument(
        "--email",
        type=Path,
        default=None,
        help="Optional path to export a plaintext email digest.",
    )
    parser.add_argument(
        "--source",
        choices=("db", "export"),
        default="db",
        help="Choose between database access or a dashboard export file.",
    )
    parser.add_argument(
        "--export-path",
        type=Path,
        default=None,
        help="Path to the dashboard export when using --source export.",
    )
    parser.add_argument(
        "--project-id",
        type=int,
        default=None,
        help="Limit the report to a single project identifier.",
    )
    parser.add_argument(
        "--json",
        type=Path,
        default=None,
        help="Optional path to write the raw summary payload as JSON.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the weekly reporting CLI."""

    args = parse_args(argv)
    projects = _load_projects_from_source(args)

    if args.project_id is not None:
        projects = [project for project in projects if project.id == args.project_id]
        if not projects:
            msg = f"No project found with id {args.project_id}"
            raise SystemExit(msg)

    summaries = [summarise_project(project) for project in projects]
    summaries.sort(key=lambda summary: summary["project_name"].lower())

    _write_markdown(args.output, summaries)
    if args.csv:
        _write_csv(args.csv, summaries)
    if args.email:
        _write_email(args.email, summaries)
    if args.json:
        _ensure_parent_directory(args.json)
        args.json.write_text(
            json.dumps(summaries, default=_serialize_dataclasses, indent=2),
            encoding="utf-8",
        )

    return 0


def _serialize_dataclasses(value):
    """JSON serializer helper for dataclasses used in summaries."""

    if isinstance(value, TaskRecord):
        return {
            "id": value.id,
            "name": value.name,
            "owner": value.owner,
            "status": value.status,
            "due_date": value.due_date.isoformat() if value.due_date else None,
            "notes": value.notes,
        }
    raise TypeError(f"Object of type {type(value)!r} is not JSON serialisable")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
