from __future__ import annotations
from typing import List, Dict, Any
from statistics import mean, pstdev
from pathlib import Path
import json

from .storage import RUNS_DIR

def summarize_pool(pool: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute very simple lineup-level metrics from the pool."""
    if not pool:
        return {"lineups": [], "pool_stats": {"count": 0}}

    projs = [float(x.get("proj", 0.0)) for x in pool]
    salaries = [int(x.get("salary", 0)) for x in pool]
    m = mean(projs)
    sd = pstdev(projs) if len(projs) > 1 else 0.0

    # rank by projection (1 = best)
    sorted_ids = [x["lineup_id"] for x in sorted(pool, key=lambda r: r.get("proj", 0.0), reverse=True)]
    rank_map = {lid: i + 1 for i, lid in enumerate(sorted_ids)}

    metrics: List[Dict[str, Any]] = []
    for ln in pool:
        proj = float(ln.get("proj", 0.0))
        sal = int(ln.get("salary", 0))
        value = proj / (sal / 1000.0) if sal > 0 else 0.0
        z = (proj - m) / sd if sd > 1e-9 else 0.0
        metrics.append({
            "lineup_id": ln["lineup_id"],
            "proj": proj,
            "salary": sal,
            "value_per_k": round(value, 3),
            "z_proj": round(z, 3),
            "proj_rank": rank_map.get(ln["lineup_id"], None),
        })

    return {
        "lineups": metrics,
        "pool_stats": {
            "count": len(pool),
            "mean_proj": round(m, 3),
            "std_proj": round(sd, 3),
            "min_salary": min(salaries),
            "max_salary": max(salaries),
        },
    }

def save_metrics(run_id: str, summary: Dict[str, Any]) -> Path:
    path = RUNS_DIR / f"{run_id}_metrics.json"
    with path.open("w") as f:
        json.dump(summary, f, indent=2)
    return path
