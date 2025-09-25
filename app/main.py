from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from uuid import uuid4
from datetime import datetime
from threading import Thread
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import csv
from io import StringIO

from .models import RunRequest, RunRecord
from .storage import save_run, load_run, list_runs
from .worker import simulate_run
from .exporter import write_fd_csv_stub
from .input_models import PlayerProjection, PlayerOwnership
from .data_storage import save_projections, save_ownership, get_inputs_info
from .pool import load_pool

app = FastAPI(title="DFS Sim Optimizer")

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

# -------- inputs (JSON) --------
@app.post("/slates/{slate_id}/projections")
def upload_projections(slate_id: str, items: List[PlayerProjection]):
    save_projections(slate_id, [i.model_dump() for i in items])
    info = get_inputs_info(slate_id)
    return {"status": "saved", "info": info}

@app.post("/slates/{slate_id}/ownership")
def upload_ownership(slate_id: str, items: List[PlayerOwnership]):
    save_ownership(slate_id, [i.model_dump() for i in items])
    info = get_inputs_info(slate_id)
    return {"status": "saved", "info": info}

# -------- inputs (CSV) --------
@app.post("/slates/{slate_id}/projections.csv")
async def upload_projections_csv(slate_id: str, file: UploadFile = File(...)):
    # Expect: player_id,name,team,position,salary,proj
    content = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(StringIO(content))
    required = {"player_id", "name", "team", "position", "salary", "proj"}
    if set(reader.fieldnames or []) < required:
        raise HTTPException(status_code=400, detail=f"CSV must include: {', '.join(sorted(required))}")
    items = []
    for row in reader:
        try:
            items.append({
                "player_id": row["player_id"],
                "name": row["name"],
                "team": row["team"],
                "position": row["position"],
                "salary": int(row["salary"]),
                "proj": float(row["proj"]),
            })
        except Exception:
            raise HTTPException(status_code=400, detail=f"Bad row: {row}")
    save_projections(slate_id, items)
    info = get_inputs_info(slate_id)
    return {"status": "saved", "rows": len(items), "info": info}

@app.post("/slates/{slate_id}/ownership.csv")
async def upload_ownership_csv(slate_id: str, file: UploadFile = File(...)):
    # Expect: player_id,own_pct
    content = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(StringIO(content))
    required = {"player_id", "own_pct"}
    if set(reader.fieldnames or []) < required:
        raise HTTPException(status_code=400, detail=f"CSV must include: {', '.join(sorted(required))}")
    items = []
    for row in reader:
        try:
            items.append({
                "player_id": row["player_id"],
                "own_pct": float(row["own_pct"]),
            })
        except Exception:
            raise HTTPException(status_code=400, detail=f"Bad row: {row}")
    save_ownership(slate_id, items)
    info = get_inputs_info(slate_id)
    return {"status": "saved", "rows": len(items), "info": info}

@app.get("/slates/{slate_id}/inputs")
def slate_inputs(slate_id: str):
    return get_inputs_info(slate_id)

# -------- runs --------
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

@app.get("/runs/{run_id}/lineups")
def get_run_lineups(run_id: str, limit: int = Query(10, ge=1, le=1000), offset: int = Query(0, ge=0)):
    pool = load_pool(run_id)
    if not pool:
        raise HTTPException(status_code=404, detail="no lineup pool found for run")
    total = len(pool)
    end = min(offset + limit, total)
    return {"total": total, "limit": limit, "offset": offset, "lineups": pool[offset:end]}

@app.get("/exports/{run_id}/fd-stub")
def export_fd_stub(run_id: str):
    rec = load_run(run_id)
    if not rec:
        raise HTTPException(status_code=404, detail="run not found")
    if rec.get("status") != "done":
        raise HTTPException(status_code=400, detail="run not finished yet")
    path = write_fd_csv_stub(run_id, n_lineups=10)
    return FileResponse(path, media_type="text/csv", filename=path.name)
