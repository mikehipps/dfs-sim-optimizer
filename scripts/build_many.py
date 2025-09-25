from optimizer.lineup_solver import Player
from optimizer.builder import build_many_lineups
from optimizer.export_fd import export_fd_csv

# --- Replace this pool with your real merged salaries+projections ---
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

# Build 10 lineups with simple caps & uniqueness and a 4-3-1 stack preference
lineups = build_many_lineups(
    pool,
    n_lineups=10,
    site_key="FD_MLB",
    global_exposure_cap=0.6,            # no player over 60% exposure across the 10
    per_player_caps=None,               # or {"p1": 0.3} for a specific player
    uniqueness_k=2,                     # at least 2 different players vs each prior LU
    stack_mode="4-3-1",                 # or "4-4" or None
    verbose=True
)

# Export for FD upload (IDs by default)
export_fd_csv(lineups, "fd_upload.csv", by="player_id")
print(f"Wrote {len(lineups)} lineups to fd_upload.csv")
