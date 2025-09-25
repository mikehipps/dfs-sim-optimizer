import time, random
from .storage import update_run, load_run
from .data_storage import get_inputs_info
from .pool import save_pool
from .metrics import summarize_pool, save_metrics
from .field_model import sample_lineup_weighted_roster
from .simulator import simulate_pool_outcomes, save_simstats

def _dedupe_key(lineup):
    return tuple(sorted(p["player_id"] for p in lineup["players"]))

def simulate_run(run_id: str, n_steps: int = 12, delay_s: float = 0.05) -> None:
    update_run(run_id, status="running", message="starting simulation", progress=0.0)
    try:
        rec = load_run(run_id)
        if not rec:
            update_run(run_id, status="error", message="run record missing")
            return

        slate_id    = rec.get("slate_id", "")
        target_pool = int(rec.get("pool_size", 50))
        salary_cap  = int(rec.get("salary_cap", 40000))
        min_stack   = int(rec.get("min_stack", 0))
        avoid_hvp   = bool(rec.get("avoid_hvp", False))
        n_sims      = int(rec.get("n_sims", 1000))
        field_size  = int(rec.get("field_size", max(200, target_pool * 20)))
        corr_sigma  = float(rec.get("corr_sigma", 1.5))
        site        = str(rec.get("site", "FD")).upper()

        info = get_inputs_info(slate_id)
        if not info.get("has_projections") or not info.get("has_ownership"):
            update_run(run_id, status="error", message=f"missing inputs for {slate_id} (projections and ownership required)", progress=0.0)
            return

        max_trials  = target_pool * 40
        seed = sum(ord(c) for c in run_id) & 0xFFFFFFFF
        rng = random.Random(seed)

        # --- Build pool ---
        pool = []
        seen = set()
        trials = 0
        while len(pool) < target_pool and trials < max_trials:
            trials += 1
            ln = sample_lineup_weighted_roster(
                slate_id, rng,
                salary_cap=salary_cap,
                min_stack=min_stack,
                avoid_hvp=avoid_hvp,
                site=site,
            )
            sig = _dedupe_key(ln)
            if sig in seen:
                continue
            seen.add(sig)
            lineup_id = f"L{len(pool)+1:03}"
            pool.append({"lineup_id": lineup_id, "players": ln["players"], "salary": ln["salary"], "proj": ln["proj"]})
            update_run(run_id, progress=min(0.45, len(pool)/target_pool*0.45), message=f"sampling {len(pool)}/{target_pool}")

        save_pool(run_id, pool)
        update_run(run_id, progress=0.5, message="pool saved")

        # --- Metrics ---
        summary = summarize_pool(pool)
        save_metrics(run_id, summary)
        update_run(run_id, progress=0.65, message="metrics computed")

        # --- Outcome sims ---
        simstats = simulate_pool_outcomes(
            pool,
            n_sims=max(50, min(n_sims, 5000)),
            field_size=max(100, field_size),
            corr_sigma=float(corr_sigma),
            seed=seed,
        )
        save_simstats(run_id, simstats)
        update_run(run_id, progress=0.9, message="outcomes simulated")

        # --- Finalize ---
        for step in range(1, n_steps + 1):
            time.sleep(delay_s)
            update_run(run_id, progress=0.9 + 0.1 * (step / n_steps), message=f"finalizing {step}/{n_steps}")

        update_run(run_id, status="done", message="finished", progress=1.0)
    except Exception as e:
        update_run(run_id, status="error", message=str(e))
