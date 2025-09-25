"use client";
import React, { useEffect, useMemo, useState } from 'react';
import RunFilters from '../../../components/RunFilters';

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type RunLite = { run_id: string; slate_id: string; n_sims: number; status: string; progress: number; created_at: string };
type RunsResp = { runs: RunLite[] };
type Lineup = { lineup_id: string; salary: number; proj: number; players: { name: string; pos: string; team: string }[] };

type MetricsResp = {
  pool_stats: { count: number; mean_proj: number; std_proj: number; min_salary: number; max_salary: number };
  lineups: { lineup_id: string; proj: number; salary: number; value_per_k: number; z_proj: number; proj_rank: number }[];
};

type SimstatsResp = {
  n_sims: number;
  field_size: number;
  corr_sigma: number;
  lineups: { lineup_id: string; mean: number; stdev: number; top50_rate: number; top10_rate: number; top1_rate: number }[];
};

export default function RunsPage() {
  const [runs, setRuns] = useState<RunLite[]>([]);
  const [filtered, setFiltered] = useState<any[] | null>(null);
  const shown = useMemo(() => filtered ?? lineups, [filtered, lineups]);
const [runId, setRunId] = useState("");
  const [lineups, setLineups] = useState<Lineup[]>([]);
  const [metrics, setMetrics] = useState<MetricsResp | null>(null);
  const [simstats, setSimstats] = useState<SimstatsResp | null>(null);
  const [exportN, setExportN] = useState<number>(20); // NEW
  const [msg, setMsg] = useState("");

  async function loadRuns() {
    const r = await fetch(`${API}/runs`, { cache: "no-store" });
    if (!r.ok) return;
    const d: RunsResp = await r.json();
    setRuns(d.runs.slice(0, 10));
  }

  async function loadLineups() {
    setMsg("");
    setLineups([]);
    if (!runId) { setMsg("Enter a run_id"); return; }
    const r = await fetch(`${API}/runs/${encodeURIComponent(runId)}/lineups?limit=10&offset=0`, { cache: "no-store" });
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
    const r = await fetch(`${API}/runs/${encodeURIComponent(runId)}/metrics`, { cache: "no-store" });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      setMsg(d.detail || "Failed to fetch metrics");
      return;
    }
    const d: MetricsResp = await r.json();
    setMetrics(d);
  }

  async function loadSimstats() {
    setMsg("");
    setSimstats(null);
    if (!runId) { setMsg("Enter a run_id"); return; }
    const r = await fetch(`${API}/runs/${encodeURIComponent(runId)}/simstats`, { cache: "no-store" });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      setMsg(d.detail || "Failed to fetch simstats");
      return;
    }
    const d: SimstatsResp = await r.json();
    setSimstats(d);
  }

  useEffect(() => { loadRuns(); }, []);

  return (
    <main className="min-h-screen p-6 space-y-6">
      <h1 className="text-2xl font-bold">Runs</h1>
        <div style={{ margin: "12px 0" }}><RunFilters rows={lineups} onFiltered={setFiltered} csvName="runs_filtered.csv" /></div>

      <div className="space-y-2">
        <div className="font-medium">Recent (latest 10)</div>
        <ul className="list-disc ml-6">
          {shown.map(r => (
            <li key={r.run_id}>
              <button className="underline" onClick={() => setRunId(r.run_id)} title="Click to select this run_id">
                {r.run_id.slice(0,8)}
              </button>{" "}
              — {r.slate_id} — {r.status} — {Math.round((r.progress ?? 0)*100)}%
            </li>
          ))}
        </ul>
      </div>

      <div className="flex gap-2 items-center flex-wrap">
        <label className="text-sm">Run ID:</label>
        <input value={runId} onChange={e => setRunId(e.target.value)} className="border rounded px-2 py-1 w-[360px]" />
        <button onClick={loadLineups} className="px-3 py-1 rounded bg-blue-600 text-white">Load lineups</button>
        <button onClick={loadMetrics} className="px-3 py-1 rounded bg-emerald-600 text-white">Load metrics</button>
        <button onClick={loadSimstats} className="px-3 py-1 rounded bg-purple-700 text-white">Load simstats</button>

        {/* NEW: Export Top by Sim */}
        <span className="ml-4 text-sm">Top-by-Sim (N):</span>
        <input
          type="number"
          min={1}
          max={500}
          value={exportN}
          onChange={(e) => setExportN(Number(e.target.value))}
          className="border rounded px-2 py-1 w-20"
        />
        <a
          className={`px-3 py-1 rounded ${runId ? "bg-gray-800 text-white" : "bg-gray-300 text-gray-600 pointer-events-none"}`}
          href={runId ? `${API}/exports/${encodeURIComponent(runId)}/top-by-sim?n=${Math.max(1, Math.min(500, Number(exportN) || 20))}` : "#"}
        >
          Download
        </a>
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

      {simstats && (
        <div className="space-y-3">
          <div className="font-medium">Sim outcomes (N={simstats.n_sims}, field≈{simstats.field_size})</div>
          <div className="overflow-auto border rounded">
            <table className="min-w-full text-sm">
              <thead className="bg-purple-50">
                <tr>
                  <th className="text-left p-2">Lineup ID</th>
                  <th className="text-left p-2">Mean</th>
                  <th className="text-left p-2">StDev</th>
                  <th className="text-left p-2">Top 50%</th>
                  <th className="text-left p-2">Top 10%</th>
                  <th className="text-left p-2">Top 1%</th>
                </tr>
              </thead>
              <tbody>
                {simstats.lineups
                  .slice()
                  .sort((a,b) => b.top10_rate - a.top10_rate)
                  .slice(0, 15)
                  .map(m => (
                    <tr key={m.lineup_id} className="border-t">
                      <td className="p-2 font-mono">{m.lineup_id}</td>
                      <td className="p-2">{m.mean.toFixed(2)}</td>
                      <td className="p-2">{m.stdev.toFixed(2)}</td>
                      <td className="p-2">{(m.top50_rate*100).toFixed(1)}%</td>
                      <td className="p-2">{(m.top10_rate*100).toFixed(1)}%</td>
                      <td className="p-2">{(m.top1_rate*100).toFixed(2)}%</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <div className="text-xs text-gray-600">Sorted by Top 10% rate. Use the download to get all rows.</div>
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
                {shown.map((ln) => (
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
