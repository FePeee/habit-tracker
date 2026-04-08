import { useState, useEffect } from "react";
import { api } from "../api/client";
import ProgressTab from "./ProgressTab";

function StreakBadge({ streak }) {
  if (streak === 0) return null;
  return (
    <span style={{ fontSize: 12, background: streak >= 7 ? "#FAEEDA" : "#E1F5EE", color: streak >= 7 ? "#633806" : "#085041", padding: "2px 8px", borderRadius: 12, fontWeight: 500 }}>
      {streak >= 7 ? "🔥" : "✦"} {streak}d
    </span>
  );
}

export default function Dashboard({ user, onLogout }) {
  const [habits, setHabits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newHabit, setNewHabit] = useState("");
  const [reminderTime, setReminderTime] = useState("");
  const [adding, setAdding] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [activeTab, setActiveTab] = useState("habits"); // "habits" or "progress"

  useEffect(() => { loadHabits(); }, []);

  async function loadHabits() {
    try {
      const data = await api.getHabits();
      setHabits(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  async function handleComplete(id) {
    try {
      const result = await api.completeHabit(id);
      setHabits(prev => prev.map(h =>
        h.id === id ? { ...h, done_today: true, streak: result.streak ?? h.streak + 1 } : h
      ));
    } catch (e) { console.error(e); }
  }

  async function handleDelete(id) {
    if (!confirm("Delete this habit?")) return;
    try {
      await api.deleteHabit(id);
      setHabits(prev => prev.filter(h => h.id !== id));
    } catch (e) { console.error(e); }
  }

  async function handleAdd(e) {
    e.preventDefault();
    if (!newHabit.trim()) return;
    setAdding(true);
    try {
      const h = await api.createHabit(newHabit.trim(), reminderTime || null);
      setHabits(prev => [...prev, h]);
      setNewHabit("");
      setReminderTime("");
      setShowForm(false);
    } catch (e) { console.error(e); } finally { setAdding(false); }
  }

  const doneCount = habits.filter(h => h.done_today).length;
  const total = habits.length;
  const pct = total > 0 ? Math.round((doneCount / total) * 100) : 0;

  return (
    <div style={{ minHeight: "100vh", background: "#f5f5f0", fontFamily: "system-ui, sans-serif", paddingTop: "20px" }}>
      {/* Header */}
      <div style={{ margin: "0 auto", background: "#fff", border: "0.5px solid #e0ddd4", borderRadius: "12px", padding: "14px 24px", maxWidth: 680, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span style={{ fontWeight: 500, fontSize: 16 }}>Habit Tracker</span>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <span style={{ fontSize: 13, color: "#888" }}>Hi, {user.name}</span>
          <button onClick={onLogout} style={{ fontSize: 13, color: "#888", background: "none", border: "none", cursor: "pointer" }}>Logout</button>
        </div>
      </div>

      <div style={{ maxWidth: 680, margin: "0 auto", paddingTop: "20px" }}>

        {/* Link code banner */}
        {user.link_code && (
          <div style={{ background: "#E1F5EE", border: "0.5px solid #5DCAA5", borderRadius: 12, padding: "14px 18px", marginBottom: 20 }}>
            <p style={{ fontSize: 13, color: "#085041", fontWeight: 500, marginBottom: 4 }}>Link your Telegram account</p>
            <p style={{ fontSize: 13, color: "#0F6E56" }}>
              Send this to the bot: <strong>/start {user.link_code}</strong>
            </p>
          </div>
        )}

        {/* Stats row */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0,1fr))", gap: 10, marginBottom: 20 }}>
          {[
            { label: "Total habits", value: total },
            { label: "Done today", value: `${doneCount}/${total}` },
            { label: "Today's rate", value: `${pct}%` },
          ].map(s => (
            <div key={s.label} style={{ background: "#fff", border: "0.5px solid #e0ddd4", borderRadius: 12, padding: "14px 16px" }}>
              <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>{s.label}</div>
              <div style={{ fontSize: 22, fontWeight: 500 }}>{s.value}</div>
            </div>
          ))}
        </div>

        {/* Tab navigation */}
        <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
          <button
            onClick={() => setActiveTab("habits")}
            style={{ 
              flex: 1, padding: "10px 16px", borderRadius: 10, border: "none",
              background: activeTab === "habits" ? "#1D9E75" : "#fff",
              color: activeTab === "habits" ? "#fff" : "#888",
              fontSize: 13, cursor: "pointer", fontWeight: 500,
              boxShadow: activeTab === "habits" ? "0 2px 8px rgba(29,158,117,0.3)" : "none"
            }}
          >
            📋 Habits
          </button>
          <button
            onClick={() => setActiveTab("progress")}
            style={{ 
              flex: 1, padding: "10px 16px", borderRadius: 10, border: "none",
              background: activeTab === "progress" ? "#6366F1" : "#fff",
              color: activeTab === "progress" ? "#fff" : "#888",
              fontSize: 13, cursor: "pointer", fontWeight: 500,
              boxShadow: activeTab === "progress" ? "0 2px 8px rgba(99,102,241,0.3)" : "none"
            }}
          >
            📈 AI Progress
          </button>
        </div>

        {/* Tab content */}
        {activeTab === "habits" ? (
          <div>
            {/* Habits list */}
            <div style={{ background: "#fff", border: "0.5px solid #e0ddd4", borderRadius: 12, overflow: "hidden", marginBottom: 16 }}>
          <div style={{ padding: "14px 18px", borderBottom: "0.5px solid #e0ddd4", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontWeight: 500, fontSize: 14 }}>Today's habits</span>
            <button
              onClick={() => setShowForm(!showForm)}
              style={{ fontSize: 13, color: "#1D9E75", background: "none", border: "0.5px solid #1D9E75", borderRadius: 8, padding: "5px 12px", cursor: "pointer", fontWeight: 500 }}
            >
              + Add habit
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleAdd} style={{ padding: "14px 18px", borderBottom: "0.5px solid #e0ddd4", display: "flex", gap: 8, flexWrap: "wrap" }}>
              <input
                placeholder="Habit name"
                value={newHabit}
                onChange={e => setNewHabit(e.target.value)}
                required
                style={{ flex: 2, minWidth: 140, padding: "8px 12px", borderRadius: 8, border: "0.5px solid #ccc", fontSize: 13 }}
              />
              <input
                type="time"
                value={reminderTime}
                onChange={e => setReminderTime(e.target.value)}
                style={{ flex: 1, minWidth: 100, padding: "8px 12px", borderRadius: 8, border: "0.5px solid #ccc", fontSize: 13 }}
              />
              <button
                type="submit"
                disabled={adding}
                style={{ padding: "8px 16px", borderRadius: 8, border: "none", background: "#1D9E75", color: "#fff", fontSize: 13, cursor: "pointer" }}
              >
                {adding ? "..." : "Save"}
              </button>
            </form>
          )}

          {loading ? (
            <div style={{ padding: 32, textAlign: "center", color: "#888", fontSize: 14 }}>Loading...</div>
          ) : habits.length === 0 ? (
            <div style={{ padding: 32, textAlign: "center", color: "#888", fontSize: 14 }}>
              No habits yet. Add your first one above!
            </div>
          ) : (
            habits.map(h => (
              <div key={h.id} style={{ padding: "14px 18px", borderBottom: "0.5px solid #f0ede4", display: "flex", alignItems: "center", gap: 12 }}>
                <button
                  onClick={() => !h.done_today && handleComplete(h.id)}
                  style={{
                    width: 24, height: 24, borderRadius: 6, border: `1.5px solid ${h.done_today ? "#1D9E75" : "#ccc"}`,
                    background: h.done_today ? "#1D9E75" : "transparent",
                    cursor: h.done_today ? "default" : "pointer",
                    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0
                  }}
                >
                  {h.done_today && <span style={{ color: "#fff", fontSize: 13, lineHeight: 1 }}>✓</span>}
                </button>
                <span style={{ flex: 1, fontSize: 14, color: h.done_today ? "#888" : "#1a1a1a", textDecoration: h.done_today ? "line-through" : "none" }}>
                  {h.name}
                </span>
                {h.reminder_time && (
                  <span style={{ fontSize: 12, color: "#aaa" }}>{h.reminder_time}</span>
                )}
                <StreakBadge streak={h.streak} />
                <button
                  onClick={() => handleDelete(h.id)}
                  style={{ fontSize: 16, color: "#ccc", background: "none", border: "none", cursor: "pointer", padding: "0 4px" }}
                >
                  ×
                </button>
              </div>
            ))
          )}
        </div>
          </div>
        ) : (
          <ProgressTab />
        )}
      </div>
    </div>
  );
}
