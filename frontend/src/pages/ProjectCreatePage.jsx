import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { useSession } from "../App.jsx";
import { api } from "../api.js";
import ProjectForm from "../components/ProjectForm.jsx";

export default function ProjectCreatePage() {
  const { user } = useSession();
  const navigate = useNavigate();
  const [employees, setEmployees] = useState([]);
  const [teams, setTeams] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    let isMounted = true;
    Promise.all([api.fetchEmployees(), api.fetchTeams(), api.fetchClients()])
      .then(([employeesRes, teamsRes, clientsRes]) => {
        if (!isMounted) return;
        setEmployees(employeesRes.employees || []);
        setTeams(teamsRes.teams || []);
        setClients(clientsRes.clients || []);
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

  const handleCreateProject = async (payload) => {
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      const response = await api.createProject(payload);
      setSuccess("Project created successfully. Redirecting...");
      setTimeout(() => {
        navigate(`/projects/${response.project.id}`);
      }, 800);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page narrow">
      <h1>Create Project</h1>
      <p className="muted">Fill in project metadata to get started.</p>
      {error ? <div className="alert-error">{error}</div> : null}
      {success ? <div className="alert-success">{success}</div> : null}
      {loading ? (
        <div className="loader">
          <span className="spinner" /> Loading form data...
        </div>
      ) : (
        <div className="card">
          <ProjectForm
            employees={employees}
            teams={teams}
            clients={clients}
            currentUser={user}
            submitting={submitting}
            onSubmit={handleCreateProject}
          />
        </div>
      )}
    </div>
  );
}
