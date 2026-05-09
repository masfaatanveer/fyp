import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";

interface LogEntry {
  id: number;
  roll_no: string;
  query: string;
  response: string;
  actor_used: string;
  created_at: string;
}

interface StatsData {
  total: number;
  by_actor: Record<string, number>;
  unique_students: number;
}

const ACTOR_CLASS: Record<string, string> = {
  academics_actor:  "actor-academics",
  lms_actor:        "actor-lms",
  admin_actor:      "actor-admin",
  admissions_actor: "actor-admissions",
};

function ActorBadge({ actor }: { actor: string }) {
  const cls = ACTOR_CLASS[actor] ?? "actor-default";
  const label = actor.replace("_actor", "").replace("_", " ") || "—";
  return <span className={`actor-badge ${cls}`}>{label}</span>;
}

function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function AdminDashboard({ apiBase = "http://127.0.0.1:8000/api/agent" }) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(false);

  async function fetchLogs() {
    setLoading(true);
    try {
      const url = filter
        ? `${apiBase}/admin/logs/?roll_no=${encodeURIComponent(filter)}&limit=100`
        : `${apiBase}/admin/logs/?limit=100`;
      const res = await fetch(url);
      const data = await res.json();
      setLogs(data.logs ?? []);
    } catch {
      setLogs([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchLogs(); }, [filter]);

  const stats: StatsData = {
    total: logs.length,
    unique_students: new Set(logs.map((l) => l.roll_no)).size,
    by_actor: logs.reduce<Record<string, number>>((acc, l) => {
      const k = l.actor_used || "unknown";
      acc[k] = (acc[k] ?? 0) + 1;
      return acc;
    }, {}),
  };

  return (
    <div className="admin-shell">
      <div className="admin-header">
        <div>
          <p className="eyebrow">KFUEIT Agent Assist</p>
          <h1>Admin Dashboard</h1>
        </div>
        <button className="admin-refresh-btn" onClick={fetchLogs} disabled={loading}>
          <RefreshCw size={14} style={{ marginRight: 6, verticalAlign: "middle" }} />
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      <div className="admin-stats">
        <div className="stat-card">
          <p>Total Queries</p>
          <strong>{stats.total}</strong>
        </div>
        <div className="stat-card">
          <p>Unique Students</p>
          <strong>{stats.unique_students}</strong>
        </div>
        {Object.entries(stats.by_actor).map(([actor, count]) => (
          <div className="stat-card" key={actor}>
            <p>{actor.replace("_actor", "").replace("_", " ")}</p>
            <strong>{count}</strong>
          </div>
        ))}
      </div>

      <div className="admin-filter">
        <input
          placeholder="Filter by roll number..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        />
      </div>

      <div className="admin-table-wrap">
        {logs.length === 0 ? (
          <p className="admin-empty">
            {loading ? "Loading logs..." : "No logs found."}
          </p>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Roll No</th>
                <th>Actor</th>
                <th>Query</th>
                <th>Response</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td style={{ whiteSpace: "nowrap", color: "var(--text-muted)", fontSize: "0.78rem" }}>
                    {timeAgo(log.created_at)}
                  </td>
                  <td style={{ fontFamily: "monospace", fontSize: "0.78rem", color: "var(--text-muted)" }}>
                    {log.roll_no}
                  </td>
                  <td><ActorBadge actor={log.actor_used} /></td>
                  <td style={{ maxWidth: 200 }}>{log.query}</td>
                  <td style={{ maxWidth: 280, color: "var(--text-muted)", fontSize: "0.82rem" }}>
                    {log.response.length > 120 ? log.response.slice(0, 120) + "…" : log.response}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
