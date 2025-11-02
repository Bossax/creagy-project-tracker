import { useState } from "react";

export default function ProjectForm({
  employees,
  teams,
  clients,
  currentUser,
  onSubmit,
  submitting = false,
}) {
  const [form, setForm] = useState({
    name: "",
    projectManagerId: currentUser?.id ?? "",
    teamId: "",
    clientId: "",
    clientName: "",
    budget: "",
    startDate: "",
    endDate: "",
  });

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    onSubmit({
      ...form,
      projectManagerId: form.projectManagerId ? Number(form.projectManagerId) : null,
      teamId: form.teamId ? Number(form.teamId) : null,
      clientId: form.clientId ? Number(form.clientId) : null,
      budget: form.budget ? Number(form.budget) : 0,
    });
  };

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="form-grid">
        <label>
          Project Name
          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            placeholder="Project name"
          />
        </label>
        <label>
          Project Manager
          <select
            name="projectManagerId"
            value={form.projectManagerId}
            onChange={handleChange}
            required
          >
            <option value="">Select manager</option>
            {employees.map((employee) => (
              <option key={employee.id} value={employee.id}>
                {employee.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Team
          <select name="teamId" value={form.teamId} onChange={handleChange} required>
            <option value="">Select team</option>
            {teams.map((team) => (
              <option key={team.id} value={team.id}>
                {team.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Existing Client
          <select name="clientId" value={form.clientId} onChange={handleChange}>
            <option value="">Select client</option>
            {clients.map((client) => (
              <option key={client.id} value={client.id}>
                {client.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          New Client Name
          <input
            name="clientName"
            value={form.clientName}
            onChange={handleChange}
            placeholder="Create new client"
          />
        </label>
        <label>
          Budget (THB)
          <input
            type="number"
            min="0"
            step="0.01"
            name="budget"
            value={form.budget}
            onChange={handleChange}
            placeholder="0"
          />
        </label>
        <label>
          Start Date
          <input type="date" name="startDate" value={form.startDate} onChange={handleChange} required />
        </label>
        <label>
          End Date
          <input type="date" name="endDate" value={form.endDate} onChange={handleChange} required />
        </label>
      </div>
      <div className="form-actions">
        <button className="btn-primary" type="submit" disabled={submitting}>
          {submitting ? "Creating..." : "Create Project"}
        </button>
      </div>
    </form>
  );
}
