import { useState } from "react";

const STATUS_OPTIONS = ["Planned", "In Progress", "Completed"];

export default function TaskForm({
  employees,
  months,
  activities,
  onSubmit,
  submitting = false,
}) {
  const [form, setForm] = useState({
    name: "",
    assigneeId: "",
    manday: "",
    budget: "",
    status: STATUS_OPTIONS[0],
  });
  const [rows, setRows] = useState([{ monthId: "", activityId: "" }]);
  const [error, setError] = useState("");

  const handleFieldChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleRowChange = (index, key, value) => {
    setRows((prev) =>
      prev.map((row, rowIndex) => (rowIndex === index ? { ...row, [key]: value } : row)),
    );
  };

  const handleAddRow = () => {
    setRows((prev) => [...prev, { monthId: "", activityId: "" }]);
  };

  const handleRemoveRow = (index) => {
    setRows((prev) => (prev.length === 1 ? prev : prev.filter((_, rowIndex) => rowIndex !== index)));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    setError("");
    const activitiesPayload = rows
      .filter((row) => row.monthId && row.activityId)
      .map((row) => ({
        monthId: Number(row.monthId),
        activityId: Number(row.activityId),
      }));
    if (activitiesPayload.length === 0) {
      setError("At least one month/activity pair is required.");
      return;
    }
    const submission = onSubmit({
      name: form.name.trim(),
      assigneeId: form.assigneeId ? Number(form.assigneeId) : null,
      manday: form.manday ? Number(form.manday) : 0,
      budget: form.budget ? Number(form.budget) : 0,
      status: form.status,
      activities: activitiesPayload,
    });
    submission
      .then(() => {
        setError("");
        setForm({
          name: "",
          assigneeId: "",
          manday: "",
          budget: "",
          status: STATUS_OPTIONS[0],
        });
        setRows([{ monthId: "", activityId: "" }]);
      })
      .catch((err) => {
        setError(err.message);
      });
    return submission;
  };

  return (
    <form className="form task-form" onSubmit={handleSubmit}>
      {error ? <div className="alert-error">{error}</div> : null}
      <div className="form-grid">
        <label>
          Task Name
          <input
            name="name"
            value={form.name}
            onChange={handleFieldChange}
            required
            placeholder="Task name"
            disabled={submitting}
          />
        </label>
        <label>
          Assignee
          <select
            name="assigneeId"
            value={form.assigneeId}
            onChange={handleFieldChange}
            required
            disabled={submitting}
          >
            <option value="">Select employee</option>
            {employees.map((employee) => (
              <option key={employee.id} value={employee.id}>
                {employee.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Manday
          <input
            name="manday"
            type="number"
            min="0"
            step="0.1"
            value={form.manday}
            onChange={handleFieldChange}
            disabled={submitting}
          />
        </label>
        <label>
          Budget (THB)
          <input
            name="budget"
            type="number"
            min="0"
            step="0.01"
            value={form.budget}
            onChange={handleFieldChange}
            disabled={submitting}
          />
        </label>
        <label>
          Status
          <select name="status" value={form.status} onChange={handleFieldChange} disabled={submitting}>
            {STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="activity-grid">
        <div className="activity-grid-header">
          <h3>Timeline &amp; Activities</h3>
          <button type="button" className="btn-secondary" onClick={handleAddRow} disabled={submitting}>
            Add Month
          </button>
        </div>
        {rows.map((row, index) => (
          <div key={index} className="activity-grid-row">
            <label>
              Month
              <select
                value={row.monthId}
                onChange={(event) => handleRowChange(index, "monthId", event.target.value)}
                required
                disabled={submitting}
              >
                <option value="">Select month</option>
                {months.map((month) => (
                  <option key={month.id} value={month.id}>
                    {month.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Activity Type
              <select
                value={row.activityId}
                onChange={(event) => handleRowChange(index, "activityId", event.target.value)}
                required
                disabled={submitting}
              >
                <option value="">Select activity</option>
                {activities.map((activity) => (
                  <option key={activity.id} value={activity.id}>
                    {activity.type}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="btn-text"
              onClick={() => handleRemoveRow(index)}
              disabled={rows.length === 1 || submitting}
            >
              Remove
            </button>
          </div>
        ))}
      </div>

      <div className="form-actions">
        <button className="btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Saving..." : "Create Task"}
        </button>
      </div>
    </form>
  );
}
