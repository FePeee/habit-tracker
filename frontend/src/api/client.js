const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getToken() {
  return localStorage.getItem("token");
}

async function request(path, options = {}) {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(err.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  register: (email, password, name) =>
    request("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),

  login: async (email, password) => {
    const form = new FormData();
    form.append("username", email);
    form.append("password", password);
    const res = await fetch(`${BASE}/api/auth/login`, { method: "POST", body: form });
    if (!res.ok) throw new Error("Invalid credentials");
    return res.json();
  },

  me: () => request("/api/auth/me"),

  getHabits: () => request("/api/habits"),

  createHabit: (name, reminder_time) =>
    request("/api/habits", {
      method: "POST",
      body: JSON.stringify({ name, reminder_time }),
    }),

  completeHabit: (id) =>
    request(`/api/habits/${id}/complete`, { method: "POST" }),

  deleteHabit: (id) =>
    request(`/api/habits/${id}`, { method: "DELETE" }),

  // AI Insights
  getAIInsights: () => request("/api/ai-insights"),

  getHabitAdvice: (habit_name, issue) =>
    request("/api/ai-habit-advice", {
      method: "POST",
      body: JSON.stringify({ habit_name, issue }),
    }),

  getRoleModelHabits: (role_or_profession, existing_habits = []) =>
    request("/api/ai-role-model-habits", {
      method: "POST",
      body: JSON.stringify({ role_or_profession, existing_habits }),
    }),

  getSuggestHabits: (goal = null) =>
    request("/api/ai-suggest-habits", {
      method: "POST",
      body: JSON.stringify({ goal }),
    }),

  deleteAIInsight: (id) =>
    request(`/api/ai-insights/${id}`, { method: "DELETE" }),
};
