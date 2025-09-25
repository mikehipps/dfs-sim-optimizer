from dataclasses import dataclass
from typing import Dict, List, Set

@dataclass(frozen=True)
class SiteRules:
    salary_cap: int
    roster_order: List[str]              # e.g. ["P","C1B","2B","3B","SS","OF","OF","OF","UTIL"]
    slot_positions: Dict[str, Set[str]]  # allowed positions per slot
    team_max_hitters: int                # FD default: 4
    hitters_slots: Set[str]              # which slots count as hitters

SITE_CONFIG: Dict[str, SiteRules] = {
    "FD_MLB": SiteRules(
        salary_cap=35_000,
        roster_order=["P","C1B","2B","3B","SS","OF","OF","OF","UTIL"],
        slot_positions={
            "P": {"P"},
            "C1B": {"C","1B","C/1B"},
            "2B": {"2B"},
            "3B": {"3B"},
            "SS": {"SS"},
            "OF": {"OF"},
            "UTIL": {"C","1B","2B","3B","SS","OF","C/1B"},
        },
        team_max_hitters=4,
        hitters_slots={"C1B","2B","3B","SS","OF","UTIL"},
    )
}
