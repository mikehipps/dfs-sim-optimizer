from __future__ import annotations
from typing import List, Dict, Optional, Set, Tuple
from math import floor

from optimizer.lineup_solver import solve_single_lineup, Player

def _index_players(pool: List[Player]) -> Dict[str, int]:
    return {p.player_id: i for i, p in enumerate(pool)}

def _lineup_player_ids(lineup: Dict[str, Player]) -> Set[str]:
    return {p.player_id for p in lineup.values()}

def _compute_max_uses(
    pool: List[Player],
    n_lineups: int,
    global_cap: float,
    per_player_caps: Optional[Dict[str, float]]
) -> Dict[str, int]:
    caps: Dict[str, int] = {}
    for p in pool:
        cap_f = per_player_caps.get(p.player_id, global_cap) if per_player_caps else global_cap
        cap_f = max(0.0, min(1.0, cap_f))
        caps[p.player_id] = floor(cap_f * n_lineups)
    return caps

def build_many_lineups(
    pool: List[Player],
    n_lineups: int = 150,
    site_key: str = "FD_MLB",
    *,
    global_exposure_cap: float = 1.0,
    per_player_caps: Optional[Dict[str, float]] = None,  # {player_id: 0.30} -> 30%
    uniqueness_k: int = 2,  # require at least k different players vs EACH previous lineup
    stack_mode: Optional[str] = None,  # None | "4-4" | "4-3-1"
    verbose: bool = True
) -> List[Dict[str, Player]]:
    """
    Returns a list of lineup dicts (slot -> Player).
    - uniqueness_k: k=2 means overlap <= roster_size - 2 (i.e., at least 2 different players).
    - stack_mode: Only "4-4" or "4-3-1" for FD (8 hitters). None disables stacking constraints.
    """
    # Basic validation
    if stack_mode not in (None, "4-4", "4-3-1"):
        raise ValueError("stack_mode must be None, '4-4', or '4-3-1'")

    id_to_idx = _index_players(pool)
    used_count: Dict[str, int] = {p.player_id: 0 for p in pool}
    max_uses: Dict[str, int] = _compute_max_uses(pool, n_lineups, global_exposure_cap, per_player_caps)

    lineups: List[Dict[str, Player]] = []
    player_overlap_cuts: List[Tuple[Set[int], int]] = []  # [(set(player_idx), max_overlap)]

    # Determine roster size (FD MLB = 9 slots)
    # We can infer by solving 1 lineup without extra cuts to read slot count,
    # but cheaper: FD MLB roster size is 9; otherwise we’ll derive post-first lineup.
    roster_size_hint = 9 if site_key == "FD_MLB" else None

    for k in range(n_lineups):
        # Build exclusion set for players who hit their exposure cap
        exclude_ids = {pid for pid, cnt in used_count.items() if cnt >= max_uses[pid]}

        # Prepare overlap cuts in index space
        overlap_cuts_idx: List[Tuple[Set[int], int]] = []
        if uniqueness_k and lineups:
            # max overlap per prior lineup = roster_size - uniqueness_k
            max_overlap = (roster_size_hint or 9) - uniqueness_k
            if max_overlap < 0:
                max_overlap = 0
            for prev in lineups:
                prev_ids = _lineup_player_ids(prev)
                prev_idx = {id_to_idx[pid] for pid in prev_ids if pid in id_to_idx}
                overlap_cuts_idx.append((prev_idx, max_overlap))

        # Try to solve; if infeasible, progressively relax uniqueness for this lineup only
        solved = False
        try_uniqueness = uniqueness_k
        while not solved:
            try:
                lu = solve_single_lineup(
                    pool,
                    site_key=site_key,
                    exclude_ids=exclude_ids,
                    player_overlap_cuts=overlap_cuts_idx,
                    stack_mode=stack_mode
                )
                # Got one
                lineups.append(lu)
                if roster_size_hint is None:
                    roster_size_hint = len(lu)
                # Update exposure counters
                for pid in _lineup_player_ids(lu):
                    used_count[pid] += 1
                solved = True
            except Exception as e:
                # If uniqueness too tight, relax down to zero for this lineup
                if try_uniqueness > 0:
                    try_uniqueness -= 1
                    if verbose:
                        print(f"[builder] relaxing uniqueness to {try_uniqueness} for lineup {k+1}")
                    # rebuild overlap_cuts_idx with updated max_overlap
                    overlap_cuts_idx = []
                    max_overlap = (roster_size_hint or 9) - try_uniqueness
                    if max_overlap < 0:
                        max_overlap = 0
                    for prev in lineups:
                        prev_ids = _lineup_player_ids(prev)
                        prev_idx = {id_to_idx[pid] for pid in prev_ids if pid in id_to_idx}
                        overlap_cuts_idx.append((prev_idx, max_overlap))
                    continue
                else:
                    # As a last resort, try ignoring exposure caps for this solve (but keep already exhausted exclusions)
                    if verbose:
                        print(f"[builder] failed with uniqueness=0. Stopping early at {len(lineups)} lineups. Reason: {e}")
                    return lineups

    return lineups
