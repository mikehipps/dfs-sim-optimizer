# pip install pulp
from typing import Dict, List, Iterable, Tuple, Optional, Set
from dataclasses import dataclass
import pulp as pl

from optimizer.site_config import SITE_CONFIG, SiteRules

@dataclass
class Player:
    player_id: str
    name: str
    team: str
    positions: Iterable[str]  # e.g. ["C/1B"] or ["OF"]
    salary: int
    projection: float

def _pos_tokens(pos_iter: Iterable[str]) -> List[str]:
    out = set()
    for p in pos_iter:
        for t in str(p).split("/"):
            out.add(t.strip())
    return sorted(out)

def preflight(pool: List[Player], rules: SiteRules) -> Tuple[bool, str]:
    # 1) at least one eligible player per slot
    pos_map = {}
    for s in rules.roster_order:
        allowed = rules.slot_positions[s]
        pos_map.setdefault(s, 0)
        for plr in pool:
            if _pos_tokens(plr.positions) and (set(_pos_tokens(plr.positions)) & allowed):
                pos_map[s] += 1
    missing = [s for s, cnt in pos_map.items() if cnt == 0]
    if missing:
        return False, f"No eligible players for slots: {missing}"

    # 2) min-salary feasibility check
    min_cost = 0
    for s in rules.roster_order:
        allowed = rules.slot_positions[s]
        cheapest = min(
            (plr.salary for plr in pool if set(_pos_tokens(plr.positions)) & allowed),
            default=None,
        )
        if cheapest is None:
            return False, f"No eligible players for slot {s}"
        min_cost += cheapest
    if min_cost > rules.salary_cap:
        return False, f"Min-salary lineup costs {min_cost} > cap {rules.salary_cap}"
    return True, "ok"

def solve_single_lineup(
    pool: List[Player],
    site_key: str = "FD_MLB",
    *,
    exclude_ids: Optional[Set[str]] = None,
    player_overlap_cuts: Optional[List[Tuple[Set[int], int]]] = None,  # [(player_idx_set, max_allowed_overlap)]
    stack_mode: Optional[str] = None  # None | "4-4" | "4-3-1" (FD only)
) -> Dict[str, Player]:
    rules = SITE_CONFIG[site_key]
    ok, msg = preflight(pool, rules)
    if not ok:
        raise ValueError(f"Infeasible before solve: {msg}")

    if stack_mode not in (None, "4-4", "4-3-1"):
        raise ValueError("stack_mode must be None, '4-4', or '4-3-1'")

    slots = list(rules.roster_order)
    players = list(pool)
    nP, nS = len(players), len(slots)

    # Decision vars: x[p_i, slot] in {0,1}
    x = pl.LpVariable.dicts("x", (range(nP), range(nS)), 0, 1, cat="Binary")

    m = pl.LpProblem("lineup", pl.LpMaximize)
    # Objective: sum(projection * assigned)
    m += pl.lpSum(players[i].projection * x[i][j] for i in range(nP) for j in range(nS))

    # Slot must be filled by exactly one player
    for j, slot in enumerate(slots):
        m += pl.lpSum(x[i][j] for i in range(nP)) == 1, f"one_per_slot_{slot}_{j}"

    # A player appears in at most one slot
    for i in range(nP):
        m += pl.lpSum(x[i][j] for j in range(nS)) <= 1, f"unique_player_{i}"

    # Eligibility: if player not eligible for slot, force 0
    for i, p in enumerate(players):
        p_pos = set(_pos_tokens(p.positions))
        for j, slot in enumerate(slots):
            if not (p_pos & rules.slot_positions[slot]):
                m += x[i][j] == 0, f"ineligible_{i}_{j}"

    # Salary cap
    m += pl.lpSum(players[i].salary * x[i][j] for i in range(nP) for j in range(nS)) <= rules.salary_cap, "cap"

    # Team max hitters (hitters slots only)
    hitters_idx = [j for j, s in enumerate(slots) if s in rules.hitters_slots]
    teams = sorted(set(p.team for p in players))
    for t in teams:
        m += pl.lpSum(
            x[i][j]
            for i, p in enumerate(players)
            for j in hitters_idx
            if p.team == t
        ) <= rules.team_max_hitters, f"team_max_hitters_{t}"

    # Exclude specific player IDs (exposure caps enforcement upstream)
    if exclude_ids:
        for i, p in enumerate(players):
            if p.player_id in exclude_ids:
                m += pl.lpSum(x[i][j] for j in range(nS)) == 0, f"exclude_{p.player_id}"

    # Uniqueness cuts: limit overlap with prior lineups by player count (not slot-specific)
    if player_overlap_cuts:
        L = len(slots)
        for cut_idx, (player_idx_set, max_overlap) in enumerate(player_overlap_cuts):
            max_overlap = max(0, min(L, int(max_overlap)))
            m += pl.lpSum(
                x[i][j] for i in player_idx_set for j in range(nS)
            ) <= max_overlap, f"overlap_cut_{cut_idx}"

    # Stacking (FD MLB):
    # "4-4": two different teams must each have >=4 hitters
    # "4-3-1": one team >=4 hitters and a different team >=3 hitters
    if stack_mode:
        # define team hitter counts
        team_to_idx = {t: k for k, t in enumerate(teams)}
        # Binary selectors for primary & (maybe) secondary team
        y = pl.LpVariable.dicts("primary", teams, lowBound=0, upBound=1, cat="Binary")
        z = pl.LpVariable.dicts("secondary", teams, lowBound=0, upBound=1, cat="Binary")

        # One primary
        m += pl.lpSum(y[t] for t in teams) == 1, "one_primary"
        # One secondary
        m += pl.lpSum(z[t] for t in teams) == 1, "one_secondary"
        # Must be different teams
        for t in teams:
            m += y[t] + z[t] <= 1, f"primary_secondary_distinct_{t}"

        # Team hitter counts
        # c_t = sum over hitters slots of x[i,j] for team t
        # Enforce minima via c_t >= min * y_t (and z_t)
        for t in teams:
            c_t = pl.lpSum(
                x[i][j]
                for i, p in enumerate(players)
                for j in hitters_idx
                if p.team == t
            )
            # Primary always >= 4
            m += c_t >= 4 * y[t], f"primary_min4_{t}"
            if stack_mode == "4-4":
                # Secondary also >= 4
                m += c_t >= 4 * z[t], f"secondary_min4_{t}"
            elif stack_mode == "4-3-1":
                # Secondary >= 3
                m += c_t >= 3 * z[t], f"secondary_min3_{t}"

    status = m.solve(pl.PULP_CBC_CMD(msg=False))
    if pl.LpStatus[status] != "Optimal":
        raise RuntimeError(f"Solver status: {pl.LpStatus[status]} — try relaxing constraints/exposures/uniqueness")

    # Build lineup dict slot->Player (label OF1..OF3 for display)
    used: Dict[str, Player] = {}
    of_counter = 1
    for j, slot in enumerate(slots):
        sel = [i for i in range(nP) if pl.value(x[i][j]) > 0.5]
        assert len(sel) == 1
        pick = players[sel[0]]
        label = slot
        if slot == "OF":
            label = f"OF{of_counter}"
            of_counter += 1
        used[label] = pick
    return used
