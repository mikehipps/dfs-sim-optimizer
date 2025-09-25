from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Optional
import csv
import pandas as pd
from math import floor

from optimizer.lineup_solver import Player
from optimizer.export_fd import export_fd_csv

INTERNAL_ORDER = ["P","C1B","2B","3B","SS","OF1","OF2","OF3","UTIL"]

@dataclass
class SelectorConfig:
    portfolio_size: int = 150
    global_exposure_cap: float = 1.0
    per_player_caps: Optional[Dict[str, float]] = None
    uniqueness_k: int = 2
    objective: str = "p99"
    secondary_objective: Optional[str] = "top_1pct_rate"
    secondary_weight: float = 0.2
    by: str = "player_id"

def load_players_csv(path: str) -> Dict[str, Player]:
    id2player: Dict[str, Player] = {}
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            positions = row["positions"].split("|") if row["positions"] else []
            id2player[row["player_id"]] = Player(
                player_id=row["player_id"],
                name=row.get("name",""),
                team=row.get("team",""),
                positions=positions,
                salary=int(float(row.get("salary",0))),
                projection=float(row.get("projection",0.0))
            )
    return id2player

def load_candidates_csv(path: str) -> List[Dict[str, str]]:
    lineups: List[Dict[str,str]] = []
    with open(path, newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            lu = {slot: row[slot] for slot in INTERNAL_ORDER}
            lineups.append(lu)
    return lineups

def _make_sets(lineups_pid: List[Dict[str,str]]) -> List[Set[str]]:
    return [set(lu.values()) for lu in lineups_pid]

def _max_uses_for_player(pid: str, K: int, cfg: SelectorConfig) -> int:
    cap = cfg.global_exposure_cap
    if cfg.per_player_caps and pid in cfg.per_player_caps:
        cap = cfg.per_player_caps[pid]
    cap = max(0.0, min(1.0, cap))
    return floor(cap * K)

def select_portfolio(
    metrics: pd.DataFrame,
    lineups_pid: List[Dict[str,str]],
    players_by_id: Dict[str, Player],
    cfg: SelectorConfig
) -> List[int]:
    assert len(metrics) == len(lineups_pid), "metrics and candidates size mismatch"
    n = len(lineups_pid)
    roster_size = len(INTERNAL_ORDER)

    score = metrics[cfg.objective].astype(float).copy()
    if cfg.secondary_objective and cfg.secondary_objective in metrics.columns:
        score = score + cfg.secondary_weight * metrics[cfg.secondary_objective].astype(float)
    order = score.sort_values(ascending=False).index.tolist()

    selected: List[int] = []
    used_counts: Dict[str,int] = {}
    max_uses_cache: Dict[str,int] = {}
    lineup_sets = _make_sets(lineups_pid)

    def can_add(idx: int) -> bool:
        if cfg.uniqueness_k > 0:
            for s_idx in selected:
                overlap = len(lineup_sets[idx] & lineup_sets[s_idx])
                if overlap > (roster_size - cfg.uniqueness_k):
                    return False
        for pid in lineup_sets[idx]:
            if pid not in max_uses_cache:
                max_uses_cache[pid] = _max_uses_for_player(pid, cfg.portfolio_size, cfg)
            if used_counts.get(pid, 0) >= max_uses_cache[pid]:
                return False
        return True

    for idx in order:
        if len(selected) >= cfg.portfolio_size:
            break
        if can_add(idx):
            selected.append(idx)
            for pid in lineup_sets[idx]:
                used_counts[pid] = used_counts.get(pid, 0) + 1

    return selected

def export_selected(
    selected_indices: List[int],
    lineups_pid: List[Dict[str,str]],
    players_by_id: Dict[str, Player],
    out_csv: str,
    by: str = "player_id"
) -> None:
    lineups_players = []
    for i in selected_indices:
        lu = lineups_pid[i]
        lu_players = {slot: players_by_id[pid] for slot, pid in lu.items()}
        lineups_players.append(lu_players)
    export_fd_csv(lineups_players, out_csv, by=by)

def exposures_report(
    selected_indices: List[int],
    lineups_pid: List[Dict[str,str]],
    players_by_id: Dict[str, Player]
) -> pd.DataFrame:
    counts: Dict[str,int] = {}
    for i in selected_indices:
        for pid in lineups_pid[i].values():
            counts[pid] = counts.get(pid, 0) + 1
    rows = []
    total = len(selected_indices)
    for pid, cnt in sorted(counts.items(), key=lambda kv: kv[1], reverse=True):
        p = players_by_id.get(pid)
        rows.append({
            "player_id": pid,
            "name": getattr(p, "name", ""),
            "team": getattr(p, "team", ""),
            "uses": cnt,
            "exposure_pct": cnt / max(1,total)
        })
    return pd.DataFrame(rows)
