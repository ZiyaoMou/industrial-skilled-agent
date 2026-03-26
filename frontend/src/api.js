const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8001";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  getCategories: () => request("/api/task-categories"),
  createCategory: (payload) => request("/api/task-categories", { method: "POST", body: JSON.stringify(payload) }),
  updateCategory: (id, payload) => request(`/api/task-categories/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  getTasks: () => request("/api/tasks"),
  createTask: (payload) => request("/api/tasks", { method: "POST", body: JSON.stringify(payload) }),
  getTaskMessages: (taskId) => request(`/api/tasks/${taskId}/messages`),
  postTaskMessage: (taskId, payload) => request(`/api/tasks/${taskId}/messages`, { method: "POST", body: JSON.stringify(payload) }),
  getSkills: () => request("/api/skills"),
  updateSkill: (skillId, payload) => request(`/api/skills/${skillId}`, { method: "PUT", body: JSON.stringify(payload) }),
  analyzeSkillLab: (payload) => request("/api/skill-lab/analyze", { method: "POST", body: JSON.stringify(payload) }),
  applySkillProposal: (payload) => request("/api/skill-lab/apply", { method: "POST", body: JSON.stringify(payload) }),
};

