from __future__ import annotations
import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from optimizer.lineup_solver import Player
from optimizer.site_config import SITE_CONFIG

# -------- Correlated sampler (simple, fast, upgradable)

def simulate_player_points(
    pool: List[Player],
    n_sims: int = 2000,
    *,
    team_sigma: float = 0.35,   # shared team boost/drag for hitters
    indiv_sigma: float = 0.45,  # idiosyncratic noise
    seed: int = 123
) -> Tuple[np.ndarray, Dict[str,int]]:
    """
    Returns:
      sim_points: [n_players, n_sims] simulated fantasy points
      index: {player_id -> row_index}
    Model:
      hitters: proj * (1 + team_factor[team] + epsilon_i)
      pitchers: proj * (1 + epsilon_i)
      clipped at 0
    Upgrade later: game env, pitcher-vs-batters anti-corr, weather, park.
    """
    rng = np.random.default_rng(seed)
    nP = len(pool)
    idx = {p.player_id: i for i, p in enumerate(pool)}
    sim = np.zeros((nP, n_sims), dtype=np.float32)

    # group indices by team and role (hitter vs pitcher)
    team_to_rows: Dict[str, List[int]] = {}
    hitter_rows: List[int] = []
    pitcher_rows: List[int] = []

    for i, p in enumerate(pool):
        is_pitcher = any("P" == t for pos in p.positions for t in str(pos).split("/"))
        (pitcher_rows if is_pitcher else hitter_rows).append(i)
        team_to_rows.setdefault(p.team, []).append(i)

    # team factors (shared) apply to hitters only
    teams = sorted(team_to_rows.keys())
    team_factors = rng.normal(loc=0.0, scale=team_sigma, size=(len(teams), n_sims))
    t_index = {t: k for k, t in enumerate(teams)}

    # per-player noise
    eps = rng.normal(loc=0.0, scale=indiv_sigma, size=(nP, n_sims))

    base = np.array([max(0.0, p.projection) for p in pool], dtype=np.float32).reshape(nP, 1)

    # apply model
    sim[:] = base + 0.0  # copy
    if hitter_rows:
        hr = np.array(hitter_rows, dtype=int)
        tf = np.stack([team_factors[t_index[pool[i].team]] for i in hr], axis=0)
        sim[hr, :] = base[hr, :] * (1.0 + tf + eps[hr, :])
    if pitcher_rows:
        pr = np.array(pitcher_rows, dtype=int)
        sim[pr, :] = base[pr, :] * (1.0 + eps[pr, :])

    # clamp to >= 0
    np.maximum(sim, 0.0, out=sim)
    return sim, idx

# -------- Scoring and metrics

def score_lineups(
    lineups: List[Dict[str, Player]],
    idx: Dict[str,int],
    sim_points: np.ndarray
) -> np.ndarray:
    """
    Returns lineup_totals: [n_lineups, n_sims]
    """
    nL, nS = len(lineups), sim_points.shape[1]
    totals = np.zeros((nL, nS), dtype=np.float32)
    for r, lu in enumerate(lineups):
        rows = [idx[p.player_id] for p in lu.values()]
        totals[r, :] = sim_points[rows, :].sum(axis=0)
    return totals

def lineup_metrics(
    lineup_totals: np.ndarray,
    top_fracs: Tuple[float, ...] = (0.50, 0.10, 0.01)
) -> pd.DataFrame:
    """
    Compute mean, std, p75/p90/p99 and topX% hit rates across sims,
    where "topX%" is relative to the candidate pool size in that run.
    """
    nL, nS = lineup_totals.shape
    means = lineup_totals.mean(axis=1)
    stds  = lineup_totals.std(axis=1)
    p75   = np.percentile(lineup_totals, 75, axis=1)
    p90   = np.percentile(lineup_totals, 90, axis=1)
    p99   = np.percentile(lineup_totals, 99, axis=1)

    # ranks per sim (higher is better)
    # argsort twice gets ranks; we compute descending ranks
    order = np.argsort(lineup_totals, axis=0)           # ascending
    ranks = np.empty_like(order)
    for c in range(nS):
        ranks[order[:, c], c] = np.arange(nL)           # 0..nL-1
    # convert to "position from top": 0 is best
    top_pos = (nL - 1) - ranks

    data = {
        "mean": means,
        "std": stds,
        "p75": p75,
        "p90": p90,
        "p99": p99,
    }
    for frac in top_fracs:
        thresh = np.floor(frac * nL).astype(int)
        hits = (top_pos <= (thresh - 1)).sum(axis=1) / nS
        data[f"top_{int(frac*100)}pct_rate"] = hits

    return pd.DataFrame(data)
