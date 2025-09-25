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

def sample_lineup_weighted_roster(
    slate_id: str,
    rng: random.Random,
    salary_cap: int = 40000,
    min_stack: int = 0,
    avoid_hvp: bool = False,
) -> Dict[str, Any]:
    """
    Contest-like sampler:
      Roster = 1P + [1B, 2B, 3B, SS, OF, OF, OF]
      Ownership-weighted choices, no duplicates, enforce salary_cap.
      If min_stack>0, ensure at least min_stack hitters from one team.
      NOTE: avoid_hvp is a placeholder until we have matchup data.
    """
    proj, own_map = _load_inputs(slate_id)
    if not proj:
        raise ValueError("no projections loaded")

    PITCHERS = [p for p in proj if p.get("position","").upper() == "P"]
    H = [p for p in proj if p.get("position","").upper() != "P"]
    by_pos = {}
    for p in H:
        by_pos.setdefault(p.get("position","").upper(), []).append(p)
    if not PITCHERS:
        raise ValueError("no pitchers in projections")
    for need in ["1B","2B","3B","SS","OF"]:
        if need != "OF" and len(by_pos.get(need, [])) == 0:
            raise ValueError(f"need at least one {need}")
    if len(by_pos.get("OF", [])) < 3:
        raise ValueError("need at least 3 OF")

    roster_slots = ["1B","2B","3B","SS","OF","OF","OF"]

    # Build team pools for hitters
    team_hitters: Dict[str, List[Dict[str, Any]]] = {}
    for h in H:
        team_hitters.setdefault(h.get("team","UNK"), []).append(h)
    teams = list(team_hitters.keys())

    # pick a stack team (weighted by count of eligible hitters)
    def pick_stack_team() -> str:
        counts = [len(team_hitters[t]) for t in teams]
        total = sum(counts) or 1
        weights = [c/total for c in counts]
        return rng.choices(teams, weights=weights, k=1)[0]

    # Try a bunch of attempts to satisfy stack + cap
    for _attempt in range(300):
        # pitcher
        pid_list = [p["player_id"] for p in PITCHERS]
        p_probs = _weights(pid_list, own_map)
        pitcher = rng.choices(PITCHERS, weights=p_probs, k=1)[0]

        chosen_ids = {pitcher["player_id"]}
        lineup = [pitcher]

        # (placeholder) avoid_hvp: we don't have matchups yet, so we can't disallow opponents specifically.
        # We leave this for later when schedule/opponents are available.

        # choose stack team if requested
        stack_team = pick_stack_team() if min_stack > 0 else None
        stack_needed = max(0, min_stack)

        # fill hitters by slot; first try to use stack team when possible
        for slot in roster_slots:
            pool = [pl for pl in by_pos[slot] if pl["player_id"] not in chosen_ids]
            if not pool:
                break

            # prefer stack team while we still need stack hitters and eligible exist
            if stack_team and stack_needed > 0:
                pool_team = [pl for pl in pool if pl.get("team") == stack_team]
                if pool_team:
                    ids = [pl["player_id"] for pl in pool_team]
                    probs = _weights(ids, own_map)
                    pick = rng.choices(pool_team, weights=probs, k=1)[0]
                    chosen_ids.add(pick["player_id"])
                    lineup.append(pick)
                    stack_needed -= 1
                    continue  # go next slot

            # otherwise pick from full pool
            ids = [pl["player_id"] for pl in pool]
            probs = _weights(ids, own_map)
            pick = rng.choices(pool, weights=probs, k=1)[0]
            chosen_ids.add(pick["player_id"])
            lineup.append(pick)

        else:
            # all slots filled; check stack + cap
            if min_stack > 0:
                stack_hits = sum(1 for x in lineup if x is not None and x.get("team")==stack_team and x.get("position","").upper()!="P")
                if stack_hits < min_stack:
                    continue  # fail this attempt and retry

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

    raise ValueError("failed to build lineup with requested constraints; raise salary_cap or lower min_stack")
