import random
from typing import Dict, Any, List
from statistics import mean, pstdev
from pathlib import Path
import json

from .storage import RUNS_DIR

def _player_sd(proj: float) -> float:
    # Simple variance model: ~30% of mean, but at least 1 pt SD
    return max(1.0, 0.30 * float(proj))

def _is_hitter(pos: str) -> bool:
    return str(pos).upper() != "P"

def simulate_pool_outcomes(
    pool: List[Dict[str, Any]],
    n_sims: int = 200,
    field_size: int = 1000,
    corr_sigma: float = 1.5,  # team bump SD applied per hitter
    seed: int | None = None,
) -> Dict[str, Any]:
    """
    For each sim:
      - Draw a team bump ~ N(0, corr_sigma) for every team (hitters only).
      - Each player gets a score ~ N(proj, sd(proj)).
      - Lineup score = sum(player scores) + sum(team bumps for hitters in the lineup).
      - Field is approximated by sampling 'field_size' lineup scores from the pool (with replacement).
      - Track finish rates: top 50%, top 10%, top 1% vs sampled field.
    """
    if seed is not None:
        rng = random.Random(seed)
    else:
        rng = random.Random()

    n_pool = len(pool)
    if n_pool == 0:
        return {"n_sims": 0, "field_size": field_size, "corr_sigma": corr_sigma, "lineups": []}

    # Pre-extract per-lineup player tuples for speed
    L_players = []
    all_teams = set()
    for ln in pool:
        players = [
            (
                float(p.get("proj", 0.0)),
                str(p.get("pos", "")),
                str(p.get("team", "")),
            )
            for p in ln.get("players", [])
        ]
        L_players.append(players)
        for _, pos, team in players:
            if _is_hitter(pos):
                all_teams.add(team)

    # Accumulators
    sums = [0.0] * n_pool
    sqs  = [0.0] * n_pool
    c50  = [0]   * n_pool
    c10  = [0]   * n_pool
    c01  = [0]   * n_pool

    for _ in range(n_sims):
        # Team correlation bumps this sim
        team_bump = {t: rng.gauss(0.0, corr_sigma) for t in all_teams}

        # Lineup scores this sim
        scores = []
        for i in range(n_pool):
            sc = 0.0
            for proj, pos, team in L_players[i]:
                sc += rng.gauss(proj, _player_sd(proj))
                if _is_hitter(pos):
                    sc += team_bump.get(team, 0.0)
            scores.append(sc)

        # Approximate field by sampling from these scores
        field_scores = [scores[rng.randrange(n_pool)] for _ in range(field_size)]
        field_scores.sort()
        q50 = field_scores[int(0.50 * (field_size - 1))]
        q90 = field_scores[int(0.90 * (field_size - 1))]
        q99 = field_scores[int(0.99 * (field_size - 1))]

        # Update accumulators
        for i, sc in enumerate(scores):
            sums[i] += sc
            sqs[i]  += sc * sc
            if sc >= q50: c50[i] += 1
            if sc >= q90: c10[i] += 1
            if sc >= q99: c01[i] += 1

    # Summarize per-lineup
    out_lineups = []
    for ln, s, q, n, t50, t10, t01 in zip(pool, sums, sqs, [n_sims]*n_pool, c50, c10, c01):
        mu = s / n if n > 0 else 0.0
        var = (q / n) - (mu * mu) if n > 0 else 0.0
        sd = var**0.5 if var > 0 else 0.0
        out_lineups.append({
            "lineup_id": ln.get("lineup_id"),
            "mean": round(mu, 3),
            "stdev": round(sd, 3),
            "top50_rate": round(t50 / n, 3) if n > 0 else 0.0,
            "top10_rate": round(t10 / n, 3) if n > 0 else 0.0,
            "top1_rate":  round(t01 / n, 3) if n > 0 else 0.0,
        })

    return {
        "n_sims": n_sims,
        "field_size": field_size,
        "corr_sigma": corr_sigma,
        "lineups": out_lineups,
    }

def save_simstats(run_id: str, stats: Dict[str, Any]) -> Path:
    p = RUNS_DIR / f"{run_id}_simstats.json"
    with p.open("w") as f:
        json.dump(stats, f, indent=2)
    return p
