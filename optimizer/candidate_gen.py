from __future__ import annotations
import random
from typing import List, Dict, Set, Tuple, Optional
from copy import deepcopy

from optimizer.site_config import SITE_CONFIG
from optimizer.lineup_solver import Player, solve_single_lineup

# -------- Helpers

def _canon_slot(slot: str) -> str:
    # Treat OF1/OF2/OF3 as the canonical "OF" slot
    return "OF" if slot.startswith("OF") else slot

def _dedupe_key(lineup: Dict[str, Player]) -> Tuple[str, ...]:
    # order-independent identity: sorted player_ids
    return tuple(sorted(p.player_id for p in lineup.values()))

def _total_salary(lineup: Dict[str, Player]) -> int:
    return sum(p.salary for p in lineup.values())

def _team_counts(lineup: Dict[str, Player], hitters_slots: Set[str]) -> Dict[str, int]:
    # Count only hitter slots (OF1/2/3 are mapped to "OF")
    c: Dict[str, int] = {}
    for slot, pl in lineup.items():
        if _canon_slot(slot) in hitters_slots:
            c[pl.team] = c.get(pl.team, 0) + 1
    return c

def _eligible_players_for_slot(pool: List[Player], allowed: Set[str]) -> List[int]:
    idxs = []
    for i, p in enumerate(pool):
        pos_tokens = set(t.strip() for s in p.positions for t in str(s).split("/"))
        if pos_tokens & allowed:
            idxs.append(i)
    return idxs

def _build_slot_index(pool: List[Player], site_key: str):
    rules = SITE_CONFIG[site_key]
    slot_to_idx: Dict[str, List[int]] = {}
    # Map by canonical slot names (so "OF" covers OF1/2/3)
    for slot in rules.roster_order:
        can = _canon_slot(slot)
        slot_to_idx[can] = _eligible_players_for_slot(pool, rules.slot_positions[can])
    return slot_to_idx

def _parse_minima(spec: Optional[str]) -> Optional[Tuple[int,int]]:
    """
    Accepts None, '4-4', '4-3-1', or generic 'A-B' like '2-2'.
    Returns (primary_min, secondary_min) or None.
    """
    if spec is None:
        return None
    s = spec.strip()
    if s == "4-4":
        return (4, 4)
    if s == "4-3-1":
        return (4, 3)
    if "-" in s:
        parts = [p.strip() for p in s.split("-")]
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            return (int(parts[0]), int(parts[1]))
    raise ValueError("preserve_stack_min must be None, '4-4', '4-3-1', or like '2-2'")

# -------- Seed generation via solver (with projection jitter to diversify)

def _jitter_pool(pool: List[Player], sigma_frac: float, rng: random.Random) -> List[Player]:
    if sigma_frac <= 0:
        return pool
    out: List[Player] = []
    for p in pool:
        jitter = 1.0 + rng.gauss(0.0, sigma_frac)
        out.append(Player(p.player_id, p.name, p.team, p.positions, p.salary, max(0.0, p.projection * jitter)))
    return out

def build_seeds_with_solver(
    pool: List[Player],
    n_seeds: int,
    site_key: str = "FD_MLB",
    *,
    stack_mode: Optional[str] = None,  # <-- default: no stacking on seeds
    uniqueness_k: int = 2,
    jitter_sigma: float = 0.10,
    max_attempts: int = 5_000,
    rng: Optional[random.Random] = None
) -> List[Dict[str, Player]]:
    """
    Use the exact solver to get high-quality diverse seeds with minimal constraints.
    """
    rng = rng or random.Random(42)
    seeds: List[Dict[str, Player]] = []
    seen: Set[Tuple[str,...]] = set()
    attempts = 0

    while len(seeds) < n_seeds and attempts < max_attempts:
        attempts += 1
        jittered = _jitter_pool(pool, jitter_sigma, rng)
        try:
            lu = solve_single_lineup(
                jittered,
                site_key=site_key,
                stack_mode=stack_mode  # None by default
            )
        except Exception:
            continue
        key = _dedupe_key(lu)
        if key in seen:
            continue
        # quick uniqueness vs previous seeds
        overlap_ok = True
        for prev in seeds:
            common = len(set(k for k in key) & set(p.player_id for p in prev.values()))
            if common > (len(lu) - uniqueness_k):
                overlap_ok = False
                break
        if not overlap_ok:
            continue
        seen.add(key)
        seeds.append(lu)
    return seeds

# -------- Massive diversification via legal one-slot swaps

def diversify_lineups(
    seeds: List[Dict[str, Player]],
    pool: List[Player],
    target_count: int,
    site_key: str = "FD_MLB",
    *,
    preserve_stack_min: Optional[str] = None,  # None (default) or 'A-B' like '2-2' (or '4-4','4-3-1')
    max_tries: int = 200_000,
    rng: Optional[random.Random] = None
) -> List[Dict[str, Player]]:
    """
    Expand seeds to a large candidate set by random legal swaps.
    If preserve_stack_min is provided, ensure the top two team hitter counts
    meet (primary_min, secondary_min).
    """
    rng = rng or random.Random(43)
    rules = SITE_CONFIG[site_key]
    slot_idx = _build_slot_index(pool, site_key)
    hitters_slots = rules.hitters_slots
    minima = _parse_minima(preserve_stack_min) if preserve_stack_min else None

    candidates: List[Dict[str, Player]] = []
    seen: Set[Tuple[str,...]] = set()
    for s in seeds:
        key = _dedupe_key(s)
        if key not in seen:
            candidates.append(deepcopy(s))
            seen.add(key)

    tries = 0
    while len(candidates) < target_count and tries < max_tries:
        tries += 1
        base = deepcopy(rng.choice(candidates))
        # choose a random lineup key (may be OF1/OF2/OF3)
        slot_ui = rng.choice(list(base.keys()))
        slot_can = _canon_slot(slot_ui)

        # pick an alternative eligible player for this (canonical) slot
        eligible = slot_idx.get(slot_can, [])
        if not eligible:
            continue
        old = base[slot_ui]
        # filter: not already in lineup
        in_ids = {p.player_id for p in base.values()}
        alt_idxs = [i for i in eligible if pool[i].player_id not in in_ids]
        if not alt_idxs:
            continue
        # bias by projection while allowing exploration
        top_idxs = sorted(alt_idxs, key=lambda i: pool[i].projection, reverse=True)[: min(10, len(alt_idxs))]
        alt = pool[rng.choice(alt_idxs if rng.random() < 0.3 else top_idxs)]

        # salary check
        new_salary = _total_salary(base) - old.salary + alt.salary
        if new_salary > rules.salary_cap:
            continue

        # team_max_hitters check if this is a hitter slot
        if slot_can in hitters_slots:
            counts = _team_counts(base, hitters_slots)
            counts[old.team] = counts.get(old.team, 0) - 1
            if counts[old.team] <= 0:
                counts.pop(old.team, None)
            counts[alt.team] = counts.get(alt.team, 0) + 1
            if counts and max(counts.values()) > rules.team_max_hitters:
                continue

        # apply swap
        base[slot_ui] = alt

        # optional minima across top two teams
        if minima:
            primary_min, secondary_min = minima
            counts = _team_counts(base, hitters_slots)
            top_two = sorted(counts.values(), reverse=True) + [0, 0]
            if not (top_two[0] >= primary_min and top_two[1] >= secondary_min):
                continue

        key = _dedupe_key(base)
        if key in seen:
            continue
        candidates.append(base)
        seen.add(key)

    return candidates
