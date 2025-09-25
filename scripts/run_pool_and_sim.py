from optimizer.lineup_solver import Player
from optimizer.candidate_gen import build_seeds_with_solver, diversify_lineups
from optimizer.sim import simulate_player_points, score_lineups, lineup_metrics
from optimizer.export_fd import export_fd_csv

import pandas as pd
import numpy as np
import csv

# --- Demo pool (replace with real merged salaries+projections) ---
pool = [
    Player("p1","Pitcher A","NYM",["P"],9500,18.2),
    Player("p2","Pitcher B","ATL",["P"],8800,17.5),
    Player("c1","C1B A","ATL",["C/1B"],3100,10.3),
    Player("c2","C1B B","NYM",["C/1B"],3200,9.9),
    Player("b2a","2B A","ATL",["2B"],2900,9.1),
    Player("b2b","2B B","NYM",["2B"],2800,8.7),
    Player("b3a","3B A","ATL",["3B"],3200,9.7),
    Player("b3b","3B B","LAD",["3B"],3500,10.0),
    Player("ss1","SS A","LAD",["SS"],3600,10.4),
    Player("ss2","SS B","NYM",["SS"],3300,9.2),
    Player("of1","OF A","LAD",["OF"],3400,9.6),
    Player("of2","OF B","NYM",["OF"],3300,9.3),
    Player("of3","OF C","ATL",["OF"],2700,7.8),
    Player("of4","OF D","ATL",["OF"],2800,8.1),
    Player("of5","OF E","LAD",["OF"],3000,8.5),
    Player("ut1","UTIL A","LAD",["1B"],2900,8.8),
    Player("ut2","UTIL B","NYM",["2B"],2500,7.1),
    Player("ut3","UTIL C","ATL",["SS"],2600,7.4),
]

# 1) Seeds — NO STACKING
seeds = build_seeds_with_solver(
    pool, n_seeds=50, site_key="FD_MLB",
    stack_mode=None, uniqueness_k=2, jitter_sigma=0.08
)
print(f"Seed lineups: {len(seeds)}")

# 2) Diversify to big candidate pool — NO STACKING
candidates = diversify_lineups(
    seeds, pool, target_count=2000, site_key="FD_MLB",
    preserve_stack_min=None
)
print(f"Candidate lineups: {len(candidates)}")

# 3) Simulate correlated player outcomes
sim_points, idx = simulate_player_points(pool, n_sims=1000, team_sigma=0.30, indiv_sigma=0.45, seed=123)

# 4) Score lineups and compute metrics
totals = score_lineups(candidates, idx, sim_points)
metrics = lineup_metrics(totals, top_fracs=(0.50, 0.10, 0.01))

# 5) Persist artifacts for selector
# 5a) lineup metrics (index aligned to candidates order)
metrics["lineup_id"] = np.arange(len(candidates))
metrics = metrics.assign(rank_p99 = (-metrics["p99"]).argsort().values + 1)
metrics.to_csv("lineup_metrics.csv", index=False)

# 5b) players.csv (id->meta)
with open("players.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["player_id","name","team","positions","salary","projection"])
    for p in pool:
        pos_str = "|".join([str(s) for s in p.positions])
        w.writerow([p.player_id, p.name, p.team, pos_str, p.salary, p.projection])

# 5c) candidates.csv (one row per lineup; player_ids; internal order)
from optimizer.export_fd import FD_UPLOAD_COLUMNS  # we only need order template
INTERNAL_ORDER = ["P","C1B","2B","3B","SS","OF1","OF2","OF3","UTIL"]
with open("candidates.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["lineup_id"] + INTERNAL_ORDER)
    for lid, lu in enumerate(candidates):
        row = [lid] + [lu[k].player_id for k in INTERNAL_ORDER]
        w.writerow(row)

# 6) Small demo upload (top 5 by p99)
top_idx = metrics.sort_values("p99", ascending=False).head(5).index.tolist()
export_fd_csv([candidates[i] for i in top_idx], "fd_upload_demo.csv", by="player_id")

print("Wrote lineup_metrics.csv, players.csv, candidates.csv, and fd_upload_demo.csv")
