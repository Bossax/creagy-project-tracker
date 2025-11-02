import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { api } from "../api.js";

export default function LoginPage({ onLogin }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [employees, setEmployees] = useState([]);
  const [teams, setTeams] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState("");
  const [newEmployeeName, setNewEmployeeName] = useState("");
  const [newEmployeeTeam, setNewEmployeeTeam] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let isMounted = true;
    Promise.all([api.fetchEmployees(), api.fetchTeams()])
      .then(([employeeRes, teamRes]) => {
        if (!isMounted) return;
        setEmployees(employeeRes.employees || []);
        setTeams(teamRes.teams || []);
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

  const handleExistingLogin = async (event) => {
    event.preventDefault();
    setError("");
    if (!selectedEmployee) {
      setError("Please select an employee.");
      return;
    }
    try {
      const response = await api.login(Number(selectedEmployee));
      onLogin(response.user);
      const redirectTo = location.state?.from?.pathname || "/";
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleCreateEmployee = async (event) => {
    event.preventDefault();
    setError("");
    if (!newEmployeeName.trim()) {
      setError("Employee name is required.");
      return;
    }
    try {
      const response = await api.createEmployee({
        name: newEmployeeName.trim(),
        teamId: newEmployeeTeam ? Number(newEmployeeTeam) : undefined,
      });
      onLogin(response.user);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="auth-container">
      <h1 className="page-title">Creagy Project Tracker</h1>
      {error ? <div className="alert-error">{error}</div> : null}
      <div className="auth-panels">
        <section className="panel">
          <h2>Sign In</h2>
          <form onSubmit={handleExistingLogin}>
            <label>
              Employee
              <select
                value={selectedEmployee}
                onChange={(event) => setSelectedEmployee(event.target.value)}
                disabled={loading}
              >
                <option value="">Select employee</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.name}
                  </option>
                ))}
              </select>
            </label>
            <button className="btn-primary" type="submit" disabled={loading}>
              Enter App
            </button>
          </form>
        </section>
        <section className="panel">
          <h2>Create Employee</h2>
          <form onSubmit={handleCreateEmployee}>
            <label>
              Name
              <input
                type="text"
                value={newEmployeeName}
                onChange={(event) => setNewEmployeeName(event.target.value)}
                placeholder="Employee name"
                disabled={loading}
              />
            </label>
            <label>
              Team (optional)
              <select
                value={newEmployeeTeam}
                onChange={(event) => setNewEmployeeTeam(event.target.value)}
                disabled={loading}
              >
                <option value="">Select team</option>
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </label>
            <button className="btn-secondary" type="submit" disabled={loading}>
              Create &amp; Login
            </button>
          </form>
        </section>
      </div>
      {loading ? <div className="muted">Loading employees...</div> : null}
    </div>
  );
}
