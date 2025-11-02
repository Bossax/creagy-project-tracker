const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  const { headers, ...rest } = options;
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(headers || {}),
    },
    ...rest,
  });

  if (response.status === 204) {
    return {};
  }

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message = data?.error || "Unexpected error";
    throw new Error(message);
  }

  return data;
}

export const api = {
  getSession() {
    return request("/api/session");
  },
  login(employeeId) {
    return request("/api/session", {
      method: "POST",
      body: JSON.stringify({ employeeId }),
    });
  },
  logout() {
    return request("/api/session", {
      method: "DELETE",
    });
  },
  fetchEmployees() {
    return request("/api/employees");
  },
  createEmployee(payload) {
    return request("/api/employees", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  fetchTeams() {
    return request("/api/teams");
  },
  fetchClients() {
    return request("/api/clients");
  },
  fetchActivities() {
    return request("/api/activities");
  },
  fetchMonths() {
    return request("/api/months");
  },
  fetchProjects() {
    return request("/api/projects");
  },
  createProject(payload) {
    return request("/api/projects", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  fetchProjectDetail(projectId) {
    return request(`/api/projects/${projectId}`);
  },
  createTask(projectId, payload) {
    return request(`/api/projects/${projectId}/tasks`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
