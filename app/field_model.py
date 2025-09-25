import random
from typing import Dict, List, Any, Tuple
from .data_storage import slate_dir, load_json

def _load_inputs(slate_id: str) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
    d = slate_dir(slate_id)
    proj = load_json(d / "projections.json") or []
    own_list = load_json(d / "ownership.json") or []
    own_map = {x["player_id"]: float(x.get("own_pct", 0.0)) for x in own_list}
    return proj, own_map

def _weights(ids: List[str], own_map: Dict[str, float]) -> List[float]:
    # Normalize ownership to probabilities; fallback to uniform if all zeros
    ws = [max(0.0, own_map.get(pid, 0.0)) for pid in ids]
    s = sum(ws)
    if s <= 0:
        return [1.0 / len(ids)] * len(ids)
    return [w / s for w in ws]

def sample_lineup_ownership_weighted(slate_id: str, rng: random.Random) -> Dict[str, Any]:
    """
    Super-simple sampler:
    - Choose 1 pitcher and 7 hitters.
    - Selections are weighted by ownership %, normalized within pitchers and hitters separately.
    - Ensures unique players within a lineup.
    NOTE: This is a stub; real stacking/constraints come later.
    """
    proj, own_map = _load_inputs(slate_id)
    if not proj:
        raise ValueError("no projections loaded")
    pitchers = [p for p in proj if p.get("position", "").upper() == "P"]
    hitters = [p for p in proj if p.get("position", "").upper() != "P"]
    if not pitchers:
        raise ValueError("no pitchers in projections")
    if len(hitters) < 7:
        raise ValueError("need at least 7 hitters")

    # Choose pitcher
    p_ids = [p["player_id"] for p in pitchers]
    p_probs = _weights(p_ids, own_map)
    pitcher = rng.choices(pitchers, weights=p_probs, k=1)[0]

    # Choose 7 distinct hitters
    h_ids = [h["player_id"] for h in hitters]
    h_probs = _weights(h_ids, own_map)
    chosen_hitters: List[Dict[str, Any]] = []
    # sample without replacement by iteratively drawing and zeroing prob
    avail = list(zip(hitters, h_probs))
    for _ in range(7):
        players, probs = zip(*avail)
        pick = rng.choices(list(players), weights=list(probs), k=1)[0]
        chosen_hitters.append(pick)
        # remove picked hitter
        avail = [(pl, pr) for (pl, pr) in avail if pl["player_id"] != pick["player_id"]]

    lineup_players = [pitcher] + chosen_hitters
    total_salary = int(sum(int(x.get("salary", 0)) for x in lineup_players))
    total_proj = float(sum(float(x.get("proj", 0.0)) for x in lineup_players))

    return {
        "players": [
            {
                "player_id": x["player_id"],
                "name": x["name"],
                "team": x["team"],
                "pos": x["position"],
                "salary": int(x["salary"]),
                "proj": float(x["proj"]),
            }
            for x in lineup_players
        ],
        "salary": total_salary,
        "proj": total_proj,
    }
