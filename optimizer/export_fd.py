import csv
from typing import Dict, List, Literal
from optimizer.lineup_solver import Player

# FanDuel expects these headers exactly (note the slash and repeated OF)
FD_UPLOAD_COLUMNS = ["P","C/1B","2B","3B","SS","OF","OF","OF","UTIL"]

# Our internal lineup dict uses these keys in this order
INTERNAL_ORDER = ["P","C1B","2B","3B","SS","OF1","OF2","OF3","UTIL"]

def _value(player: Player, by: Literal["player_id","name"]) -> str:
    return player.player_id if by == "player_id" else player.name

def export_fd_csv(
    lineups: List[Dict[str, Player]],
    path: str,
    by: Literal["player_id","name"]="player_id"
) -> None:
    """
    Writes CSV with FD headers (P, C/1B, 2B, 3B, SS, OF, OF, OF, UTIL).
    Pulls players from internal slots: P, C1B, 2B, 3B, SS, OF1, OF2, OF3, UTIL.
    """
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(FD_UPLOAD_COLUMNS)
        for lu in lineups:
            row = []
            for key in INTERNAL_ORDER:
                if key not in lu:
                    raise KeyError(f"Lineup missing slot {key}")
                row.append(_value(lu[key], by))
            w.writerow(row)
