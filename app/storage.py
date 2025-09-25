import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

RUNS_DIR = Path(__file__).resolve().parent / "runs"
RUNS_DIR.mkdir(parents=True, exist_ok=True)

def _path(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}.json"

def save_run(run_id: str, payload: Dict[str, Any]) -> None:
    with open(_path(run_id), "w") as f:
        json.dump(payload, f, indent=2, default=str)

def load_run(run_id: str) -> Optional[Dict[str, Any]]:
    p = _path(run_id)
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)

def update_run(run_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
    rec = load_run(run_id)
    if not rec:
        return None
    rec.update(fields)
    save_run(run_id, rec)
    return rec

def list_runs() -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for p in RUNS_DIR.glob("*.json"):
        # Skip artifacts like "<id>_pool.json" / "<id>_metrics.json"
        if "_" in p.stem:
            continue
        try:
            with open(p) as f:
                rec = json.load(f)
            if not isinstance(rec, dict):
                continue
            items.append({
                "run_id": rec.get("run_id"),
                "slate_id": rec.get("slate_id"),
                "n_sims": rec.get("n_sims"),
                "status": rec.get("status"),
                "progress": rec.get("progress"),
                "created_at": rec.get("created_at"),
            })
        except Exception:
            continue

    def _ts(x: Dict[str, Any]) -> datetime:
        try:
            v = x.get("created_at")
            if isinstance(v, str):
                return datetime.fromisoformat(v.replace("Z", ""))
        except Exception:
            pass
        return datetime.min

    items.sort(key=_ts, reverse=True)
    return items
