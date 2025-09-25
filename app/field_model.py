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
    ws = [max(0.0, own_map.get(pid, 0.0)) for pid in ids]
    s = sum(ws)
    return ([1.0 / len(ids)] * len(ids)) if s <= 0 else [w / s for w in ws]

def _is_hitter_pos(pos: str) -> bool:
    return pos.upper() != "P"

def _eligible_pool(by_pos: Dict[str, List[Dict[str, Any]]], slot: str) -> List[Dict[str, Any]]:
    s = slot.upper()
    if s == "UTIL":
        # any hitter
        all_hitters: List[Dict[str, Any]] = []
        for k, lst in by_pos.items():
            if k != "P":
                all_hitters.extend(lst)
        return all_hitters
    if s in by_pos:
        return by_pos[s]
    if s in ("C/1B", "C1B"):
        # allow either C or 1B; sample data likely only has 1B
        return (by_pos.get("C", []) or []) + (by_pos.get("1B", []) or [])
    return []

def sample_lineup_weighted_roster(
    slate_id: str,
    rng: random.Random,
    salary_cap: int = 40000,
    min_stack: int = 0,
    avoid_hvp: bool = False,
    site: str = "FD",
) -> Dict[str, Any]:
    """
    Site-aware MLB rosters:
      FD: 1P + [C/1B, 2B, 3B, SS, OF, OF, OF, UTIL] -> 9 total (8 hitters)
      DK: 2P + [C/1B, 2B, 3B, SS, OF, OF, OF, UTIL] -> 10 total (8 hitters)
    """
    proj, own_map = _load_inputs(slate_id)
    if not proj:
        raise ValueError("no projections loaded")

    PITCHERS = [p for p in proj if p.get("position","").upper() == "P"]
    H = [p for p in proj if _is_hitter_pos(p.get("position",""))]
    if not PITCHERS:
        raise ValueError("no pitchers in projections")
    if len(H) < 8:
        raise ValueError("insufficient hitters in projections")

    by_pos: Dict[str, List[Dict[str, Any]]] = {}
    for p in proj:
        pos = str(p.get("position","")).upper()
        by_pos.setdefault(pos, []).append(p)

    site_u = (site or "FD").upper()
    if site_u == "DK":
        pitcher_slots = 2
        hitter_slots = ["C/1B","2B","3B","SS","OF","OF","OF","UTIL"]
        if len(PITCHERS) < 2: raise ValueError("need at least 2 pitchers for DK")
        if len(_eligible_pool(by_pos,"OF")) < 3: raise ValueError("need at least 3 OF for DK")
    else:
        # FD
        pitcher_slots = 1
        hitter_slots = ["C/1B","2B","3B","SS","OF","OF","OF","UTIL"]
        if len(_eligible_pool(by_pos,"OF")) < 3: raise ValueError("need at least 3 OF for FD")

    # Build team -> hitters map
    team_hitters: Dict[str, List[Dict[str, Any]]] = {}
    for h in H:
        team_hitters.setdefault(h.get("team","UNK"), []).append(h)
    teams = list(team_hitters.keys())

    def pick_stack_team() -> str:
        counts = [len(team_hitters[t]) for t in teams]
        total = sum(counts) or 1
        weights = [c/total for c in counts]
        return rng.choices(teams, weights=weights, k=1)[0]

    # Try multiple attempts to satisfy stack + cap
    for _attempt in range(600):
        chosen_ids = set()
        lineup: List[Dict[str, Any]] = []

        # pitchers
        p_pool = [p for p in PITCHERS]
        for _ in range(pitcher_slots):
            ids = [p["player_id"] for p in p_pool if p["player_id"] not in chosen_ids]
            if not ids: break
            probs = _weights(ids, own_map)
            pick = rng.choices([pl for pl in p_pool if pl["player_id"] in ids], weights=probs, k=1)[0]
            chosen_ids.add(pick["player_id"])
            lineup.append(pick)
        if len([x for x in lineup if x.get("position","").upper()=="P"]) != pitcher_slots:
            continue

        # stack target
        stack_team = pick_stack_team() if min_stack > 0 else None
        stack_needed = max(0, min_stack)

        # hitters
        for slot in hitter_slots:
            pool = [pl for pl in _eligible_pool(by_pos, slot) if pl["player_id"] not in chosen_ids and _is_hitter_pos(pl.get("position",""))]
            if not pool:
                break
            if stack_team and stack_needed > 0:
                pool_team = [pl for pl in pool if pl.get("team")==stack_team]
                if pool_team:
                    ids = [pl["player_id"] for pl in pool_team]
                    probs = _weights(ids, own_map)
                    pick = rng.choices(pool_team, weights=probs, k=1)[0]
                    chosen_ids.add(pick["player_id"])
                    lineup.append(pick)
                    stack_needed -= 1
                    continue
            ids = [pl["player_id"] for pl in pool]
            probs = _weights(ids, own_map)
            pick = rng.choices(pool, weights=probs, k=1)[0]
            chosen_ids.add(pick["player_id"])
            lineup.append(pick)

        total_slots = pitcher_slots + len(hitter_slots)
        if len(lineup) != total_slots:
            continue

        if min_stack > 0:
            hits_on_stack = sum(1 for x in lineup if _is_hitter_pos(x.get("position","")) and x.get("team")==stack_team)
            if hits_on_stack < min_stack:
                continue

        total_salary = int(sum(int(x.get("salary", 0)) for x in lineup))
        if total_salary <= salary_cap:
            total_proj = float(sum(float(x.get("proj", 0.0)) for x in lineup))
            return {
                "players": [
                    {"player_id": x["player_id"], "name": x["name"], "team": x["team"], "pos": x["position"], "salary": int(x["salary"]), "proj": float(x["proj"])}
                    for x in lineup
                ],
                "salary": total_salary,
                "proj": total_proj,
            }

    raise ValueError("failed to build lineup with requested constraints; adjust cap/stack/site or inputs")
