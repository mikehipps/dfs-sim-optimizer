"use client";

import { useEffect, useRef, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
const SITE_DEFAULT_CAP: Record<"FD"|"DK", number> = { FD: 35000, DK: 50000 };

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
  const [site, setSite] = useState<"FD" | "DK">("FD");
  const [slate, setSlate] = useState("demo-mlb-2025-09-25");

  // contest knobs (NEW)
  const [contestSize, setContestSize] = useState<number>(5000);
  const [myEntries, setMyEntries] = useState<number>(1);

  const [poolSize, setPoolSize] = useState<number>(50);
  const [salaryCap, setSalaryCap] = useState<number>(SITE_DEFAULT_CAP["FD"]);
  const [minStack, setMinStack] = useState<number>(0);

  // sim controls
  const [nSims, setNSims] = useState<number>(1000);
  const [fieldSize, setFieldSize] = useState<number>(1000);
  const [corrSigma, setCorrSigma] = useState<number>(1.5);

  const [runId, setRunId] = useState<string | null>(null);
  const [rec, setRec] = useState<RunRecord | null>(null);
  const [busy, setBusy] = useState(false);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  function applyContestDefaults() {
    const cs = Math.max(50, Math.min(100000, Number(contestSize) || 1000));
    const me = Math.max(1, Math.min(150, Number(myEntries) || 1));

    // Suggest field size = contest size
    const suggestedField = cs;

    // Suggest n_sims = clamp( min(2000, max(500, 0.5 * field)) )
    const suggestedSims = Math.max(500, Math.min(2000, Math.round(0.5 * suggestedField)));

    // Suggest pool_size = clamp( max(50, entries * 12), ≤ 1000 )
    const suggestedPool = Math.max(50, Math.min(1000, me * 12));

    setFieldSize(suggestedField);
    setNSims(suggestedSims);
    setPoolSize(suggestedPool);
  }

  async function startRun() {
    setBusy(true);
    setRec(null);
    try {
      const size = Math.max(1, Math.min(1000, Number(poolSize) || 50));
      const cap = Math.max(1, Math.min(100000, Number(salaryCap) || SITE_DEFAULT_CAP[site]));
      const maxStack = 8; // both FD and DK have 8 hitters
      const stack = Math.max(0, Math.min(maxStack, Number(minStack) || 0));

      const sims = Math.max(50, Math.min(5000, Number(nSims) || 1000));
      const field = Math.max(100, Math.min(20000, Number(fieldSize) || 1000));
      const sigma = Math.max(0, Math.min(5, Number(corrSigma) || 1.5));

      const r = await fetch(`${API}/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          site,
          slate_id: slate,
          n_sims: sims,
          pool_size: size,
          salary_cap: cap,
          min_stack: stack,
          field_size: field,
          corr_sigma: sigma,
        }),
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
    if (!id) return;
    try {
      const r = await fetch(`${API}/runs/${id}`, { cache: "no-store" });
      if (!r.ok) return;
      const data: RunRecord = await r.json();
      setRec(data);
      if (data.status === "done" || data.status === "error") {
        setBusy(false);
        if (timerRef.current) {
          if (timerRef.current) {
  clearInterval(timerRef.current);
  timerRef.current = null;
}

          timerRef.current = null;
          timerRef.current = null;
        }
      }
    } catch {
      // swallow transient fetch errors; next tick will retry
    }
  }

  useEffect(() => {
    if (!runId) return;
    timerRef.current = setInterval(() => fetchRun(runId), 800);
    return () => {
      if (timerRef.current) {
          if (timerRef.current) {
  clearInterval(timerRef.current);
  timerRef.current = null;
}

          timerRef.current = null;
        timerRef.current = null;
      }
    };
  }, [runId]);

  const pct = Math.round((rec?.progress ?? 0) * 100);

  return (
    <main className="min-h-screen p-6 flex flex-col items-center gap-6">
      <h1 className="text-2xl font-bold">DFS Sim Optimizer — Minimal UI</h1>

      <div className="flex gap-3 items-center flex-wrap">
        <label className="text-sm">Site:</label>
        <select
          value={site}
          onChange={(e) => {
            const s = (e.target.value === "DK" ? "DK" : "FD") as "FD"|"DK";
            setSite(s);
            setSalaryCap(SITE_DEFAULT_CAP[s]); // auto-fill cap
          }}
          className="border rounded px-2 py-1"
        >
          <option value="FD">FD</option>
          <option value="DK">DK</option>
        </select>

        <label className="text-sm">Slate:</label>
        <input value={slate} onChange={(e) => setSlate(e.target.value)} className="border rounded px-2 py-1" />
      </div>

      {/* Contest config */}
      <div className="flex gap-3 items-center flex-wrap">
        <label className="text-sm">Contest size:</label>
        <input type="number" min={50} max={100000} value={contestSize} onChange={(e) => setContestSize(Number(e.target.value))} className="border rounded px-2 py-1 w-28" />
        <label className="text-sm">My entries:</label>
        <input type="number" min={1} max={150} value={myEntries} onChange={(e) => setMyEntries(Number(e.target.value))} className="border rounded px-2 py-1 w-24" />
        <button onClick={applyContestDefaults} className="px-3 py-1 rounded bg-gray-800 text-white">Apply defaults</button>
      </div>

      {/* Pool + sim knobs */}
      <div className="flex gap-3 items-center flex-wrap">
        <label className="text-sm">Pool size:</label>
        <input type="number" min={1} max={1000} value={poolSize} onChange={(e) => setPoolSize(Number(e.target.value))} className="border rounded px-2 py-1 w-24" />

        <label className="text-sm">Salary cap:</label>
        <input type="number" min={1000} max={100000} value={salaryCap} onChange={(e) => setSalaryCap(Number(e.target.value))} className="border rounded px-2 py-1 w-28" />

        <label className="text-sm">Min stack:</label>
        <input type="number" min={0} max={8} value={minStack} onChange={(e) => setMinStack(Number(e.target.value))} className="border rounded px-2 py-1 w-20" />

        <label className="text-sm ml-2">N sims:</label>
        <input type="number" min={50} max={5000} value={nSims} onChange={(e) => setNSims(Number(e.target.value))} className="border rounded px-2 py-1 w-24" />

        <label className="text-sm">Field size:</label>
        <input type="number" min={100} max={20000} value={fieldSize} onChange={(e) => setFieldSize(Number(e.target.value))} className="border rounded px-2 py-1 w-28" />

        <label className="text-sm">Corr σ:</label>
        <input type="number" min={0} max={5} step="0.1" value={corrSigma} onChange={(e) => setCorrSigma(Number(e.target.value))} className="border rounded px-2 py-1 w-24" />

        <button onClick={startRun} disabled={busy} className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-50">
          {busy ? "Running..." : "Start Run"}
        </button>
      </div>

      <div className="text-xs text-gray-600">
        Roster:&nbsp;
        {site === "DK"
          ? "DK = 2P, C/1B, 2B, 3B, SS, OF×3, UTIL (cap $50k)"
          : "FD = 1P, C/1B, 2B, 3B, SS, OF×3, UTIL (cap $35k)"}
      </div>

      {rec && (
        <div className="w-full max-w-xl space-y-2">
          <div className="text-sm">
            <span className="font-mono">{rec.run_id.slice(0, 8)}</span> — {rec.status} — {pct}%
          </div>
          <div className="w-full h-3 bg-gray-200 rounded">
            <div className="h-3 bg-blue-600 rounded" style={{ width: `${pct}%` }} />
          </div>
          <div className="text-xs text-gray-600">{rec.message}</div>

          {rec.status === "done" && (
            <a className="inline-block mt-2 underline text-blue-700" href={`${API}/exports/${rec.run_id}/fd-stub`}>
              Download CSV (stub)
            </a>
          )}
        </div>
      )}
    </main>
  );
}
