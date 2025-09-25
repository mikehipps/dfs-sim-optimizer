"use client";

import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type RunLite = { run_id: string; slate_id: string; n_sims: number; status: string; progress: number; created_at: string };
type RunsResp = { runs: RunLite[] };
type Lineup = { lineup_id: string; salary: number; proj: number; players: { name: string; pos: string; team: string }[] };

export default function RunsPage() {
  const [runs, setRuns] = useState<RunLite[]>([]);
  const [runId, setRunId] = useState("");
  const [lineups, setLineups] = useState<Lineup[]>([]);
  const [msg, setMsg] = useState("");

  async function loadRuns() {
    const r = await fetch(`${API}/runs`);
    const d: RunsResp = await r.json();
    setRuns(d.runs.reverse().slice(0, 10));
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
      </div>

      {msg && <div className="text-sm text-gray-700">{msg}</div>}

      {lineups.length > 0 && (
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
      )}
    </main>
  );
}
