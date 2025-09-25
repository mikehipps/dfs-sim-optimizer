"use client";

import { useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

type RunResp = { run_id: string; status: string };
type RunRecord = {
  run_id: string;
  slate_id: string;
  n_sims: number;
  status: string;
  progress: number;
  message: string;
  created_at: string;
};

export default function Home() {
  const [slate, setSlate] = useState("demo-mlb-2025-09-25");
  const [runId, setRunId] = useState<string | null>(null);
  const [rec, setRec] = useState<RunRecord | null>(null);
  const [busy, setBusy] = useState(false);
  const timerRef = useRef<NodeJS.Timer | null>(null);

  async function startRun() {
    setBusy(true);
    setRec(null);
    try {
      const r = await fetch(`${API}/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slate_id: slate, n_sims: 1000 }),
      });
      const data: RunResp = await r.json();
      setRunId(data.run_id);
    } catch (e) {
      console.error(e);
      alert("Failed to start run");
      setBusy(false);
    }
  }

  async function fetchRun(id: string) {
    const r = await fetch(`${API}/runs/${id}`);
    if (!r.ok) return;
    const data: RunRecord = await r.json();
    setRec(data);
    if (data.status === "done" || data.status === "error") {
      setBusy(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }

  useEffect(() => {
    if (!runId) return;
    timerRef.current = setInterval(() => fetchRun(runId), 300);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [runId]);

  const pct = Math.round((rec?.progress ?? 0) * 100);

  return (
    <main className="min-h-screen p-6 flex flex-col items-center gap-6">
      <h1 className="text-2xl font-bold">DFS Sim Optimizer — Minimal UI</h1>

      <div className="flex gap-2 items-center">
        <label className="text-sm">Slate:</label>
        <input
          value={slate}
          onChange={(e) => setSlate(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <button
          onClick={startRun}
          disabled={busy}
          className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50"
        >
          {busy ? "Running..." : "Start Run"}
        </button>
      </div>

      {rec && (
        <div className="w-full max-w-xl space-y-2">
          <div className="text-sm">
            <span className="font-mono">{rec.run_id.slice(0, 8)}</span> — {rec.status} — {pct}%
          </div>
          <div className="w-full h-3 bg-gray-200 rounded">
            <div
              className="h-3 bg-blue-600 rounded"
              style={{ width: `${pct}%` }}
            />
          </div>
          <div className="text-xs text-gray-600">{rec.message}</div>

          {rec.status === "done" && (
            <a
              className="inline-block mt-2 underline text-blue-700"
              href={`${API}/exports/${rec.run_id}/fd-stub`}
            >
              Download CSV (stub)
            </a>
          )}
        </div>
      )}
    </main>
  );
}
