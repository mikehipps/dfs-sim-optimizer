from optimizer.lineup_solver import solve_single_lineup, Player
from optimizer.export_fd import export_fd_csv

# Build a tiny demo pool (replace with your merged salaries+projections later)
pool = [
    Player("p1","Pitcher A","NYM",["P"],9500,18.2),
    Player("c1","C1B A","ATL",["C/1B"],3100,10.3),
    Player("b2","2B A","ATL",["2B"],2900,9.1),
    Player("b3","3B A","ATL",["3B"],3200,9.7),
    Player("ss","SS A","LAD",["SS"],3600,10.4),
    Player("of1","OF A","LAD",["OF"],3400,9.6),
    Player("of2","OF B","NYM",["OF"],3300,9.3),
    Player("of3","OF C","ATL",["OF"],2700,7.8),
    Player("ut1","UTIL A","LAD",["1B"],2900,8.8),
    Player("ut2","UTIL B","NYM",["2B"],2500,7.1),
]

lu = solve_single_lineup(pool, "FD_MLB")
export_fd_csv([lu], "fd_upload.csv", by="player_id")
print("Wrote fd_upload.csv in repo root.")
