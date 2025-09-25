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

def write_top_by_sim(run_id: str, n: int = 20) -> Path:
    """
    Create CSV of top-N lineups ranked by Top10% rate (desc),
    then Top1% (desc), then Mean (desc).
    Columns: LineupID, Top10%, Top1%, Top50%, Mean, StDev, Proj, Salary, Players
    """
    sim_p = RUNS_DIR / f"{run_id}_simstats.json"
    pool_p = RUNS_DIR / f"{run_id}_pool.json"
    if not sim_p.exists():
        raise ValueError("simstats not found; run must be finished with sim step")
    if not pool_p.exists():
        raise ValueError("pool not found for run")

    with sim_p.open() as f:
        sim = json.load(f)
    with pool_p.open() as f:
        pool = {ln["lineup_id"]: ln for ln in json.load(f)}

    # join metrics with lineup info
    rows = []
    for m in sim.get("lineups", []):
        lid = m.get("lineup_id")
        ln = pool.get(lid)
        if not ln:
            continue
        names = [f"{p['name']}({p['pos']}-{p['team']})" for p in ln.get("players", [])]
        rows.append({
            "LineupID": lid,
            "Top10%": float(m.get("top10_rate", 0.0)),
            "Top1%":  float(m.get("top1_rate", 0.0)),
            "Top50%": float(m.get("top50_rate", 0.0)),
            "Mean":   float(m.get("mean", 0.0)),
            "StDev":  float(m.get("stdev", 0.0)),
            "Proj":   float(ln.get("proj", 0.0)),
            "Salary": int(ln.get("salary", 0)),
            "Players": " | ".join(names),
        })

    rows.sort(key=lambda r: (r["Top10%"], r["Top1%"], r["Mean"]), reverse=True)
    out_path = RUNS_DIR / f"{run_id}_top10rate.csv"
    with out_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["LineupID","Top10%","Top1%","Top50%","Mean","StDev","Proj","Salary","Players"])
        for r in rows[:n]:
            w.writerow([
                r["LineupID"],
                f"{r['Top10%']:.3f}",
                f"{r['Top1%']:.4f}",
                f"{r['Top50%']:.3f}",
                f"{r['Mean']:.2f}",
                f"{r['StDev']:.2f}",
                f"{r['Proj']:.2f}",
                r["Salary"],
                r["Players"],
            ])
    return out_path
