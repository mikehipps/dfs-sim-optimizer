from fastapi import FastAPI, HTTPException
from uuid import uuid4
from datetime import datetime
from threading import Thread
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import RunRequest, RunRecord
from .storage import save_run, load_run, list_runs
from .worker import simulate_run
from .exporter import write_fd_csv_stub

app = FastAPI(title="DFS Sim Optimizer")

# allow the Next.js dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/runs")
def start_run(req: RunRequest):
    run_id = str(uuid4())
    record = RunRecord(
        run_id=run_id,
        slate_id=req.slate_id,
        n_sims=req.n_sims,
        created_at=datetime.utcnow(),
    )
    save_run(run_id, record.model_dump())
    Thread(target=simulate_run, args=(run_id,), daemon=True).start()
    return {"run_id": run_id, "status": "created"}

@app.get("/runs")
def get_runs():
    return {"runs": list_runs()}

@app.get("/runs/{run_id}")
def get_run(run_id: str):
    rec = load_run(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="run not found")
    return rec

@app.get("/exports/{run_id}/fd-stub")
def export_fd_stub(run_id: str):
    rec = load_run(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="run not found")
    if rec.get("status") != "done":
        raise HTTPException(status_code=400, detail="run not finished yet")
    path = write_fd_csv_stub(run_id, n_lineups=10)
    return FileResponse(path, media_type="text/csv", filename=path.name)
