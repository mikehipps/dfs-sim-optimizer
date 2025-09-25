import csv
from pathlib import Path
from .storage import RUNS_DIR, load_run

def write_fd_csv_stub(run_id: str, n_lineups: int = 5) -> Path:
    """Write a placeholder CSV for FanDuel/DK export (STUB FORMAT)."""
    rec = load_run(run_id)
    if not rec:
        raise ValueError("run not found")
    # Save next to run records for now
    out_path = RUNS_DIR / f"{run_id}_fd_stub.csv"
    # Minimal, not the real FD format (that comes later)
    header = ["Lineup", "Salary", "Notes"]
    rows = []
    for i in range(1, n_lineups + 1):
        lineup = f"PLAYER_A{i},PLAYER_B{i},PLAYER_C{i},... (stub)"
        salary = 50000 - i * 100  # dummy
        rows.append([lineup, salary, f"Generated from run {run_id}"])
    with out_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return out_path
