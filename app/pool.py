from typing import List, Dict, Any
from .data_storage import slate_dir, load_json
from .storage import RUNS_DIR
from pathlib import Path

def _load_projections(slate_id: str) -> List[Dict[str, Any]]:
    d = slate_dir(slate_id)
    proj = load_json(d / "projections.json") or []
    return proj

def build_pool(slate_id: str, n_lineups: int = 10) -> List[Dict[str, Any]]:
    """
    Super-simple stub:
      - pick one pitcher and 7 hitters using round-robin through sorted projections.
      - compute total salary and projected points.
    """
    proj = _load_projections(slate_id)
    if not proj:
        return []

    hitters = [p for p in proj if p.get("position", "").upper() != "P"]
    pitchers = [p for p in proj if p.get("position", "").upper() == "P"]
    if not hitters:
        hitters = proj[:]  # fallback: treat everyone as a hitter
    if not pitchers:
        # fallback: pick the highest-proj player as "pitcher"
        pitchers = [sorted(proj, key=lambda x: x.get("proj", 0.0), reverse=True)[0]]

    # sort for deterministic behavior
    hitters = sorted(hitters, key=lambda x: x.get("proj", 0.0), reverse=True)
    pitchers = sorted(pitchers, key=lambda x: x.get("proj", 0.0), reverse=True)

    pool: List[Dict[str, Any]] = []
    for i in range(n_lineups):
        p = pitchers[i % len(pitchers)]
        lineup_players = [p]  # 1 pitcher
        # 7 hitters: round-robin window through hitters
        for j in range(7):
            lineup_players.append(hitters[(i + j) % len(hitters)])

        total_salary = int(sum(int(x.get("salary", 0)) for x in lineup_players))
        total_proj = float(sum(float(x.get("proj", 0.0)) for x in lineup_players))
        pool.append({
            "lineup_id": f"L{i+1:03}",
            "players": [
                {"player_id": x["player_id"], "name": x["name"], "team": x["team"], "pos": x["position"], "salary": int(x["salary"]), "proj": float(x["proj"])}
                for x in lineup_players
            ],
            "salary": total_salary,
            "proj": total_proj,
        })
    return pool

def save_pool(run_id: str, pool: List[Dict[str, Any]]) -> Path:
    out = RUNS_DIR / f"{run_id}_pool.json"
    import json
    with out.open("w") as f:
        json.dump(pool, f, indent=2)
    return out

def load_pool(run_id: str) -> List[Dict[str, Any]]:
    p = RUNS_DIR / f"{run_id}_pool.json"
    if not p.exists():
        return []
    import json
    with p.open() as f:
        return json.load(f)
