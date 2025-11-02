import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useSession } from "../App.jsx";
import { api } from "../api.js";
import GanttChart from "../components/GanttChart.jsx";
import MandayChart from "../components/MandayChart.jsx";
import SummaryBox from "../components/SummaryBox.jsx";
import TaskForm from "../components/TaskForm.jsx";

export default function ProjectDetailPage() {
  const { projectId } = useParams();
  const { user } = useSession();
  const [detail, setDetail] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [months, setMonths] = useState([]);
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [taskSubmitting, setTaskSubmitting] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [detailRes, employeeRes, monthsRes, activitiesRes] = await Promise.all([
        api.fetchProjectDetail(projectId),
        api.fetchEmployees(),
        api.fetchMonths(),
        api.fetchActivities(),
      ]);
      setDetail(detailRes);
      setEmployees(employeeRes.employees || []);
      setMonths(monthsRes.months || []);
      setActivities(activitiesRes.activities || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleCreateTask = async (payload) => {
    setTaskSubmitting(true);
    try {
      await api.createTask(projectId, payload);
      await loadData();
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setTaskSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="loader">
        <span className="spinner" /> Loading project...
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <div className="alert-error">{error}</div>
        <Link className="btn-secondary" to="/">
          Back to dashboard
        </Link>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="page">
        <div className="alert-error">Project not found.</div>
        <Link className="btn-secondary" to="/">
          Back to dashboard
        </Link>
      </div>
    );
  }

  const project = detail.project;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>{project.name}</h1>
          <p className="muted">
            Client {project.client?.name ?? "-"} • Manager {project.projectManager?.name ?? "-"} • Team{" "}
            {project.team?.name ?? "-"}
          </p>
        </div>
        <Link className="btn-secondary" to="/">
          Back
        </Link>
      </div>

      <SummaryBox summary={detail.summary} />

      {detail.canManageTasks ? (
        <div className="card">
          <h2>Add Task</h2>
          <TaskForm
            employees={employees}
            months={months}
            activities={activities}
            submitting={taskSubmitting}
            onSubmit={handleCreateTask}
          />
        </div>
      ) : (
        <div className="muted">
          Only {project.projectManager?.name ?? "the project manager"} can add tasks to this project.
        </div>
      )}

      <div className="layout-split">
        <div className="card">
          <h2>Gantt Timeline</h2>
          <GanttChart data={detail.ganttData} />
        </div>
        <div className="card">
          <h2>Monthly Manday</h2>
          <MandayChart chart={detail.mandayChart} />
        </div>
      </div>

      <div className="card">
        <h2>Tasks</h2>
        {project.tasks && project.tasks.length > 0 ? (
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Assignee</th>
                <th>Manday</th>
                <th>Budget</th>
                <th>Status</th>
                <th>Timeline</th>
              </tr>
            </thead>
            <tbody>
              {project.tasks.map((task) => (
                <tr key={task.id}>
                  <td>{task.name}</td>
                  <td>{task.assignee?.name ?? "-"}</td>
                  <td>{task.manday}</td>
                  <td>{task.budget}</td>
                  <td>{task.status}</td>
                  <td>
                    {task.activities?.length ? (
                      <ul className="pill-list">
                        {task.activities.map((activity, index) => (
                          <li key={index}>
                            <span className="pill">{activity.month.label}</span>
                            <span className="muted tiny">{activity.activity.type}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span className="muted">No activity</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="muted">No tasks yet.</p>
        )}
      </div>
    </div>
  );
}
