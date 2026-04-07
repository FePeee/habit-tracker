import { useState, useEffect } from "react";
import { api } from "../api/client";

const typeConfig = {
  habit_advice: { emoji: "💡", label: "Habit Advice", color: "#1D9E75" },
  role_model: { emoji: "🎭", label: "Role Model", color: "#6366F1" },
  suggest_habits: { emoji: "✨", label: "Suggestions", color: "#F59E0B" },
  weekly_report: { emoji: "📊", label: "Weekly Report", color: "#EF4444" },
};

function InsightCard({ insight, onDelete }) {
  const [expanded, setExpanded] = useState(false);
  const config = typeConfig[insight.insight_type] || { emoji: "🤖", label: "Insight", color: "#888" };
  
  const dateStr = insight.created_at 
    ? new Date(insight.created_at).toLocaleDateString("en-US", { 
        month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" 
      })
    : "";

  const isLong = insight.content.length > 300;
  const displayContent = isLong && !expanded ? insight.content.slice(0, 300) + "..." : insight.content;

  return (
    <div style={{ 
      background: "#fff", 
      border: `0.5px solid ${config.color}33`, 
      borderLeft: `3px solid ${config.color}`,
      borderRadius: 8, 
      padding: "14px 16px",
      marginBottom: 12
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 18 }}>{config.emoji}</span>
          <span style={{ fontWeight: 500, fontSize: 13, color: config.color }}>{config.label}</span>
          {insight.habit_name && (
            <span style={{ fontSize: 12, color: "#888" }}>— {insight.habit_name}</span>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 11, color: "#aaa" }}>{dateStr}</span>
          <button
            onClick={() => onDelete(insight.id)}
            style={{ fontSize: 14, color: "#ccc", background: "none", border: "none", cursor: "pointer", padding: "0 4px" }}
            title="Delete"
          >
            ×
          </button>
        </div>
      </div>
      
      {insight.context && (
        <div style={{ fontSize: 12, color: "#666", marginBottom: 8, fontStyle: "italic" }}>
          📌 {insight.context}
        </div>
      )}
      
      <div style={{ fontSize: 13, lineHeight: 1.6, color: "#333", whiteSpace: "pre-wrap" }}>
        {displayContent}
      </div>
      
      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          style={{ fontSize: 12, color: config.color, background: "none", border: "none", cursor: "pointer", marginTop: 6, fontWeight: 500 }}
        >
          {expanded ? "Show less" : "Read more"}
        </button>
      )}
    </div>
  );
}

export default function ProgressTab() {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => { loadInsights(); }, []);

  async function loadInsights() {
    try {
      const data = await api.getAIInsights();
      setInsights(data);
    } catch (e) {
      console.error("Failed to load insights:", e);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete(id) {
    if (!confirm("Delete this insight?")) return;
    try {
      await api.deleteAIInsight(id);
      setInsights(prev => prev.filter(i => i.id !== id));
    } catch (e) {
      console.error("Failed to delete insight:", e);
    }
  }

  const filtered = filter === "all" 
    ? insights 
    : insights.filter(i => i.insight_type === filter);

  const typeCounts = insights.reduce((acc, i) => {
    acc[i.insight_type] = (acc[i.insight_type] || 0) + 1;
    return acc;
  }, {});

  return (
    <div>
      {/* Summary stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 10, marginBottom: 20 }}>
        <div style={{ background: "#fff", border: "0.5px solid #e0ddd4", borderRadius: 12, padding: "14px 16px" }}>
          <div style={{ fontSize: 12, color: "#888", marginBottom: 6 }}>Total insights</div>
          <div style={{ fontSize: 22, fontWeight: 500 }}>{insights.length}</div>
        </div>
        {Object.entries(typeConfig).map(([type, cfg]) => (
          typeCounts[type] > 0 && (
            <div key={type} style={{ background: "#fff", border: `0.5px solid ${cfg.color}33`, borderRadius: 12, padding: "14px 16px" }}>
              <div style={{ fontSize: 12, color: cfg.color, marginBottom: 6 }}>{cfg.emoji} {cfg.label}</div>
              <div style={{ fontSize: 22, fontWeight: 500 }}>{typeCounts[type]}</div>
            </div>
          )
        ))}
      </div>

      {/* Filter tabs */}
      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        <button
          onClick={() => setFilter("all")}
          style={{ 
            padding: "6px 14px", borderRadius: 20, border: "none", 
            background: filter === "all" ? "#1D9E75" : "#fff",
            color: filter === "all" ? "#fff" : "#888",
            fontSize: 12, cursor: "pointer", fontWeight: 500
          }}
        >
          All ({insights.length})
        </button>
        {Object.entries(typeConfig).map(([type, cfg]) => (
          typeCounts[type] > 0 && (
            <button
              key={type}
              onClick={() => setFilter(type)}
              style={{ 
                padding: "6px 14px", borderRadius: 20, border: "none", 
                background: filter === type ? cfg.color : "#fff",
                color: filter === type ? "#fff" : "#888",
                fontSize: 12, cursor: "pointer", fontWeight: 500
              }}
            >
              {cfg.emoji} {cfg.label} ({typeCounts[type]})
            </button>
          )
        ))}
      </div>

      {/* Insights list */}
      {loading ? (
        <div style={{ padding: 32, textAlign: "center", color: "#888", fontSize: 14 }}>Loading insights...</div>
      ) : filtered.length === 0 ? (
        <div style={{ 
          background: "#fff", border: "0.5px solid #e0ddd4", borderRadius: 12, 
          padding: 40, textAlign: "center" 
        }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📭</div>
          <p style={{ fontSize: 14, color: "#888", marginBottom: 8 }}>No insights yet</p>
          <p style={{ fontSize: 13, color: "#aaa" }}>
            Use the Telegram bot to get AI insights:<br/>
            <code style={{ background: "#f5f5f0", padding: "2px 6px", borderRadius: 4 }}>/advise</code>
            {" "},{" "}
            <code style={{ background: "#f5f5f0", padding: "2px 6px", borderRadius: 4 }}>/rolemodel</code>
            {" "},{" "}
            <code style={{ background: "#f5f5f0", padding: "2px 6px", borderRadius: 4 }}>/suggest</code>
            {" "},{" "}
            <code style={{ background: "#f5f5f0", padding: "2px 6px", borderRadius: 4 }}>/report</code>
          </p>
        </div>
      ) : (
        filtered.map(insight => (
          <InsightCard key={insight.id} insight={insight} onDelete={handleDelete} />
        ))
      )}
    </div>
  );
}
