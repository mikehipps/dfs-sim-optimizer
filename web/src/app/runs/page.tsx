"use client";

import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type RunLite = { run_id: string; slate_id: string; n_sims: number; status: string; progress: number; created_at: string };
type RunsResp = { runs: RunLite[] };
type Lineup = { lineup_id: string; salary: number; proj: number; players: { name: string; pos: string; team: string }[] };

type MetricsResp = {
  pool_stats: { count: number; mean_proj: number; std_proj: number; min_salary: number; max_salary: number };
  lineups: { lineup_id: string; proj: number; salary: number; value_per_k: number; z_proj: number; proj_rank: number }[];
};

export default function RunsPage() {
  const [runs, setRuns] = useState<RunLite[]>([]);
  const [runId, setRunId] = useState("");
  const [lineups, setLineups] = useState<Lineup[]>([]);
  const [metrics, setMetrics] = useState<MetricsResp | null>(null);
  const [msg, setMsg] = useState("");

  async function loadRuns() {
    const r = await fetch(`${API}/runs`);
    const d: RunsResp = await r.json();
    setRuns(d.runs.slice(0, 10)); // backend already sorts newest-first
  }

  async function loadLineups() {
    setMsg("");
    setLineups([]);
    if (!runId) { setMsg("Enter a run_id"); return; }
    const r = await fetch(`${API}/runs/${encodeURIComponent(runId)}/lineups?limit=10&offset=0`);
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      setMsg(d.detail || "Failed to fetch lineups");
      return;
    }
    const d = await r.json();
    setLineups(d.lineups || []);
    if ((d.total ?? 0) > 10) setMsg(`Showing 10 of ${d.total} (use API for more)`);
  }

  async function loadMetrics() {
    setMsg("");
    setMetrics(null);
    if (!runId) { setMsg("Enter a run_id"); return; }
    const r = await fetch(`${API}/runs/${encodeURIComponent(runId)}/metrics`);
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      setMsg(d.detail || "Failed to fetch metrics");
      return;
    }
    const d: MetricsResp = await r.json();
    setMetrics(d);
  }

  useEffect(() => { loadRuns(); }, []);

  return (
    <main className="min-h-screen p-6 space-y-6">
      <h1 className="text-2xl font-bold">Runs</h1>

      <div className="space-y-2">
        <div className="font-medium">Recent (latest 10)</div>
        <ul className="list-disc ml-6">
          {runs.map(r => (
            <li key={r.run_id}>
              <button
                className="underline"
                onClick={() => setRunId(r.run_id)}
                title="Click to select this run_id"
              >
                {r.run_id.slice(0,8)}
              </button>{" "}
              — {r.slate_id} — {r.status} — {Math.round((r.progress ?? 0)*100)}%
            </li>
          ))}
        </ul>
      </div>

      <div className="flex gap-2 items-center">
        <label className="text-sm">Run ID:</label>
        <input value={runId} onChange={e => setRunId(e.target.value)} className="border rounded px-2 py-1 w-[360px]" />
        <button onClick={loadLineups} className="px-3 py-1 rounded bg-blue-600 text-white">Load lineups</button>
        <button onClick={loadMetrics} className="px-3 py-1 rounded bg-emerald-600 text-white">Load metrics</button>
      </div>

      {msg && <div className="text-sm text-gray-700">{msg}</div>}

      {metrics && (
        <div className="space-y-3">
          <div className="font-medium">Pool stats</div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-sm">
            <div className="p-2 bg-gray-100 rounded">Count: {metrics.pool_stats.count}</div>
            <div className="p-2 bg-gray-100 rounded">Mean proj: {metrics.pool_stats.mean_proj}</div>
            <div className="p-2 bg-gray-100 rounded">Std proj: {metrics.pool_stats.std_proj}</div>
            <div className="p-2 bg-gray-100 rounded">Min salary: {metrics.pool_stats.min_salary}</div>
            <div className="p-2 bg-gray-100 rounded">Max salary: {metrics.pool_stats.max_salary}</div>
          </div>

          <div className="font-medium mt-2">Top 10 by proj_rank</div>
          <div className="overflow-auto border rounded">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="text-left p-2">Rank</th>
                  <th className="text-left p-2">Lineup ID</th>
                  <th className="text-left p-2">Proj</th>
                  <th className="text-left p-2">Salary</th>
                  <th className="text-left p-2">Value / $1k</th>
                  <th className="text-left p-2">Z (proj)</th>
                </tr>
              </thead>
              <tbody>
                {metrics.lineups
                  .slice()
                  .sort((a,b) => (a.proj_rank ?? 1e9) - (b.proj_rank ?? 1e9))
                  .slice(0,10)
                  .map(m => (
                    <tr key={m.lineup_id} className="border-t">
                      <td className="p-2">{m.proj_rank}</td>
                      <td className="p-2 font-mono">{m.lineup_id}</td>
                      <td className="p-2">{m.proj.toFixed(2)}</td>
                      <td className="p-2">{m.salary}</td>
                      <td className="p-2">{m.value_per_k.toFixed(3)}</td>
                      <td className="p-2">{m.z_proj.toFixed(3)}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {lineups.length > 0 && (
        <div className="space-y-2">
          <div className="font-medium">Sample lineups (first 10)</div>
          <div className="overflow-auto border rounded">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-100">
                <tr>
                  <th className="text-left p-2">Lineup ID</th>
                  <th className="text-left p-2">Salary</th>
                  <th className="text-left p-2">Proj</th>
                  <th className="text-left p-2">Players (first 5)</th>
                </tr>
              </thead>
              <tbody>
                {lineups.map((ln) => (
                  <tr key={ln.lineup_id} className="border-t">
                    <td className="p-2 font-mono">{ln.lineup_id}</td>
                    <td className="p-2">{ln.salary}</td>
                    <td className="p-2">{ln.proj.toFixed(2)}</td>
                    <td className="p-2">
                      {ln.players.slice(0,5).map(p => `${p.name}(${p.pos}-${p.team})`).join(" | ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </main>
  );
}
