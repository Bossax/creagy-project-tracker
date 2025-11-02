import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api.js";

export default function DashboardPage() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;
    api
      .fetchProjects()
      .then((response) => {
        if (!isMounted) return;
        setProjects(response.projects || []);
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="loader">
        <span className="spinner" /> Loading projects...
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Projects</h1>
          <p className="muted">Manage Creagy projects, tasks, and progress.</p>
        </div>
        <Link className="btn-primary" to="/projects/new">
          New Project
        </Link>
      </div>

      {error ? <div className="alert-error">{error}</div> : null}

      {projects.length === 0 ? (
        <div className="empty-state">
          <p>No projects yet. Start by creating one.</p>
          <Link className="btn-primary" to="/projects/new">
            Create Project
          </Link>
        </div>
      ) : (
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Client</th>
                <th>Project Manager</th>
                <th>Team</th>
                <th>Start</th>
                <th>End</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id}>
                  <td>
                    <Link to={`/projects/${project.id}`} className="link-strong">
                      {project.name}
                    </Link>
                  </td>
                  <td>{project.client?.name ?? "-"}</td>
                  <td>{project.projectManager?.name ?? "-"}</td>
                  <td>{project.team?.name ?? "-"}</td>
                  <td>{project.startDate}</td>
                  <td>{project.endDate}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
