"use client";

import { useState } from "react";

const API = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export default function SlatesPage() {
  const [slate, setSlate] = useState("demo-mlb-2025-09-25");
  const [projFile, setProjFile] = useState<File | null>(null);
  const [ownFile, setOwnFile] = useState<File | null>(null);
  const [log, setLog] = useState<string>("");

  async function upload(kind: "projections" | "ownership") {
    try {
      const file = kind === "projections" ? projFile : ownFile;
      if (!file) {
        alert(`Choose a ${kind} CSV first.`);
        return;
      }
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API}/slates/${encodeURIComponent(slate)}/${kind}.csv`, {
        method: "POST",
        body: form,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");
      setLog((prev) => `${prev}\n${kind} uploaded: ${JSON.stringify(data)}`);
    } catch (e: any) {
      setLog((prev) => `${prev}\nERROR ${kind}: ${e.message || e}`);
    }
  }

  async function checkInputs() {
    const res = await fetch(`${API}/slates/${encodeURIComponent(slate)}/inputs`);
    const data = await res.json();
    setLog((prev) => `${prev}\ninputs: ${JSON.stringify(data)}`);
  }

  return (
    <main className="min-h-screen p-6 space-y-6">
      <h1 className="text-2xl font-bold">Upload Slate Inputs</h1>

      <div className="flex gap-2 items-center">
        <label className="text-sm">Slate:</label>
        <input
          value={slate}
          onChange={(e) => setSlate(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <button
          onClick={checkInputs}
          className="px-3 py-1 rounded bg-gray-800 text-white"
        >
          Check
        </button>
      </div>

      <div className="space-y-3">
        <div>
          <div className="font-medium">Projections CSV (player_id,name,team,position,salary,proj)</div>
          <input type="file" accept=".csv" onChange={(e) => setProjFile(e.target.files?.[0] || null)} />
          <button
            onClick={() => upload("projections")}
            className="ml-2 px-3 py-1 rounded bg-blue-600 text-white"
          >
            Upload projections.csv
          </button>
        </div>

        <div>
          <div className="font-medium">Ownership CSV (player_id,own_pct)</div>
          <input type="file" accept=".csv" onChange={(e) => setOwnFile(e.target.files?.[0] || null)} />
          <button
            onClick={() => upload("ownership")}
            className="ml-2 px-3 py-1 rounded bg-blue-600 text-white"
          >
            Upload ownership.csv
          </button>
        </div>
      </div>

      <pre className="bg-gray-100 p-3 rounded text-sm whitespace-pre-wrap">{log}</pre>
    </main>
  );
}
