import json
from pathlib import Path
from typing import Any, Dict, List, Optional

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
    for p in sorted(RUNS_DIR.glob("*.json")):
        with open(p) as f:
            rec = json.load(f)
        items.append({
            "run_id": rec.get("run_id"),
            "slate_id": rec.get("slate_id"),
            "n_sims": rec.get("n_sims"),
            "status": rec.get("status"),
            "progress": rec.get("progress"),
            "created_at": rec.get("created_at"),
        })
    return items
