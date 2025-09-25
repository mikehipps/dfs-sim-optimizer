import csv, json
from pathlib import Path
from .storage import RUNS_DIR, load_run

def _pool_path(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}_pool.json"

def write_fd_csv_stub(run_id: str, n_lineups: int = 10) -> Path:
    """
    Export a CSV. If a lineup pool exists for this run, use it.
    Otherwise, fall back to a simple stub.
    """
    rec = load_run(run_id)
    if not rec:
        raise ValueError("run not found")

    out_path = RUNS_DIR / f"{run_id}_fd_stub.csv"
    pool_file = _pool_path(run_id)

    header = ["Lineup", "Salary", "TotalProj"]
    rows = []

    if pool_file.exists():
        with pool_file.open() as f:
            pool = json.load(f)
        for ln in pool[:n_lineups]:
            names = [f"{p['name']}({p['pos']}-{p['team']})" for p in ln.get("players", [])]
            lineup_str = " | ".join(names)
            rows.append([lineup_str, ln.get("salary", 0), f"{ln.get('proj', 0.0):.2f}"])
    else:
        # Fallback dummy rows
        for i in range(1, n_lineups + 1):
            lineup_str = f"PLAYER_A{i},PLAYER_B{i},PLAYER_C{i},... (stub)"
            rows.append([lineup_str, 50000 - i * 100, "0.00"])

    with out_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return out_path
