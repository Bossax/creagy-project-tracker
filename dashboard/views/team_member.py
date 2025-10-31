"""Team member specific view helpers."""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any, Callable, Iterable, Mapping

import streamlit as st

from ..api_client import APIClient, APIClientError

StatusNormaliser = Callable[[str | None], str]
OwnerNormaliser = Callable[[str | None], str]

_STATUS_CHOICES: tuple[str, ...] = (
    "Not Started",
    "In Progress",
    "Blocked",
    "Completed",
)

_ESTIMATE_KEYS: tuple[str, ...] = (
    "estimated_man_days",
    "man_days",
    "estimate_days",
    "effort_days",
)


def _extract_man_days(task: Mapping[str, Any]) -> float:
    """Return the estimated man-days for a task with a sensible default."""

    for key in _ESTIMATE_KEYS:
        value = task.get(key)
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:  # pragma: no cover - defensive
                continue
    return 1.0


def _format_man_days(value: float) -> str:
    """Return a compact string representation for man-day totals."""

    if value.is_integer():
        return f"{int(value)}"
    return f"{value:.1f}"


def _parse_due_date(raw_value: Any) -> date | None:
    """Convert API due date payloads into :class:`datetime.date` objects."""

    if raw_value in (None, "", "null"):
        return None
    if isinstance(raw_value, date):
        return raw_value
    if isinstance(raw_value, datetime):
        return raw_value.date()
    if isinstance(raw_value, str):
        try:
            return datetime.fromisoformat(raw_value).date()
        except ValueError:  # pragma: no cover - defensive
            return None
    return None


def _format_due_date(raw_value: Any) -> str:
    """Return a human friendly string for the due date."""

    parsed = _parse_due_date(raw_value)
    if parsed is None:
        return "—"
    return parsed.strftime("%Y-%m-%d")


def _build_task_options(tasks: Iterable[Mapping[str, Any]]) -> list[tuple[str, Mapping[str, Any]]]:
    """Return label-task pairs for selection widgets."""

    options: list[tuple[str, Mapping[str, Any]]] = []
    for task in tasks:
        identifier = task.get("id", "?")
        name = task.get("name", "Task")
        label = f"#{identifier} · {name}"
        options.append((label, task))
    return options


def _append_weekly_update(existing_notes: str | None, author: str, update: str) -> str:
    """Append a timestamped update entry to the task notes."""

    timestamp = datetime.now().strftime("%Y-%m-%d")
    entry = f"[{timestamp}] {author}: {update.strip()}"
    if existing_notes:
        existing_notes = existing_notes.rstrip()
        return f"{existing_notes}\n{entry}"
    return entry


def render_team_member_view(
    task_items: list[Mapping[str, Any]],
    *,
    controls_container: Any,
    api_client: APIClient,
    normalise_owner: OwnerNormaliser,
    normalise_status: StatusNormaliser,
) -> None:
    """Render the dashboard view for individual contributors."""

    st.subheader("My Workload")
    if not task_items:
        st.info(
            "No tasks available yet. Create tasks via the FastAPI backend to populate the list.",
        )
        return

    owners = sorted({normalise_owner(task.get("owner")) for task in task_items})
    if not owners:
        st.warning("No team members have been assigned to tasks yet.")
        return

    selected_owner = controls_container.selectbox("Team member", owners)
    filtered_tasks = [
        task for task in task_items if normalise_owner(task.get("owner")) == selected_owner
    ]

    st.markdown(
        "Review your assigned backlog, update progress, and capture weekly notes for the team."
    )

    if not filtered_tasks:
        st.warning("No tasks match the selected filters just yet.")
        return

    total_man_days = sum(_extract_man_days(task) for task in filtered_tasks)
    status_counter = Counter(normalise_status(task.get("status")) for task in filtered_tasks)

    summary_cols = st.columns(4)
    summary_cols[0].metric("Assigned Tasks", len(filtered_tasks))
    summary_cols[1].metric("Total Man-days", _format_man_days(total_man_days))
    summary_cols[2].metric("In Progress", status_counter.get("In Progress", 0))
    summary_cols[3].metric("Completed", status_counter.get("Completed", 0))

    st.markdown("### Task Details")
    display_rows = [
        {
            "ID": task.get("id", "?"),
            "Task": task.get("name", "Task"),
            "Status": normalise_status(task.get("status")),
            "Due Date": _format_due_date(task.get("due_date")),
            "Man-days": _format_man_days(_extract_man_days(task)),
            "Notes": task.get("notes", ""),
        }
        for task in filtered_tasks
    ]
    st.dataframe(display_rows, hide_index=True, use_container_width=True)

    st.markdown("### Update progress")
    task_options = _build_task_options(filtered_tasks)
    selected_label = st.selectbox(
        "Task to update",
        [label for label, _ in task_options],
    )
    selected_task = next(task for label, task in task_options if label == selected_label)

    existing_due_date = _parse_due_date(selected_task.get("due_date"))
    existing_status = normalise_status(selected_task.get("status"))
    current_notes = selected_task.get("notes")

    with st.form(f"task-update-{selected_task.get('id')}"):
        status = st.selectbox(
            "Status",
            _STATUS_CHOICES,
            index=_STATUS_CHOICES.index(existing_status)
            if existing_status in _STATUS_CHOICES
            else 0,
        )
        due_date_text = st.text_input(
            "Due date (YYYY-MM-DD)",
            value=existing_due_date.isoformat() if existing_due_date else "",
            placeholder="YYYY-MM-DD",
        )
        weekly_update = st.text_area(
            "Weekly update",
            placeholder="Share progress, blockers, or next steps.",
        )
        submitted = st.form_submit_button("Submit update")

    if submitted:
        payload: dict[str, Any] = {"status": status}
        due_date_value = due_date_text.strip()
        if due_date_value:
            try:
                due_date_iso = datetime.fromisoformat(due_date_value).date().isoformat()
            except ValueError:
                st.error("Due date must be in YYYY-MM-DD format.")
                return
            payload["due_date"] = due_date_iso
        else:
            payload["due_date"] = None
        if weekly_update.strip():
            payload["notes"] = _append_weekly_update(current_notes, selected_owner, weekly_update)
        try:
            api_client.update_task(int(selected_task.get("id")), payload)
        except (APIClientError, ValueError) as exc:
            st.error(f"Failed to update task: {exc}")
        else:
            st.success("Task updated successfully.")
            st.cache_data.clear()
            st.experimental_rerun()

    st.markdown("### Status breakdown")
    breakdown_rows = [
        {"Status": status, "Tasks": count} for status, count in sorted(status_counter.items())
    ]
    st.table(breakdown_rows)
