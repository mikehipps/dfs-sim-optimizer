import time, random
from .storage import update_run, load_run
from .data_storage import get_inputs_info
from .pool import save_pool
from .metrics import summarize_pool, save_metrics
from .field_model import sample_lineup_ownership_weighted

def _dedupe_key(lineup):
    return tuple(sorted(p["player_id"] for p in lineup["players"]))

def simulate_run(run_id: str, n_steps: int = 20, delay_s: float = 0.05) -> None:
    update_run(run_id, status="running", message="starting simulation", progress=0.0)
    try:
        rec = load_run(run_id)
        if not rec:
            update_run(run_id, status="error", message="run record missing")
            return

        slate_id = rec.get("slate_id", "")
        target_pool = int(rec.get("pool_size", 50))  # NEW
        info = get_inputs_info(slate_id)
        if not info.get("has_projections") or not info.get("has_ownership"):
            update_run(run_id, status="error", message=f"missing inputs for {slate_id} (projections and ownership required)", progress=0.0)
            return

        max_trials  = target_pool * 20
        seed = sum(ord(c) for c in run_id) & 0xFFFFFFFF
        rng = random.Random(seed)

        pool = []
        seen = set()
        trials = 0
        while len(pool) < target_pool and trials < max_trials:
            trials += 1
            ln = sample_lineup_ownership_weighted(slate_id, rng)
            sig = _dedupe_key(ln)
            if sig in seen:
                continue
            seen.add(sig)
            lineup_id = f"L{len(pool)+1:03}"
            pool.append({"lineup_id": lineup_id, "players": ln["players"], "salary": ln["salary"], "proj": ln["proj"]})
            update_run(run_id, progress=min(0.5, len(pool)/target_pool*0.5), message=f"sampling {len(pool)}/{target_pool}")

        save_pool(run_id, pool)

        summary = summarize_pool(pool)
        save_metrics(run_id, summary)
        update_run(run_id, progress=0.75, message="metrics computed")

        for step in range(1, n_steps + 1):
            time.sleep(delay_s)
            update_run(run_id, progress=0.75 + 0.25 * (step / n_steps), message=f"finalizing {step}/{n_steps}")

        update_run(run_id, status="done", message="finished", progress=1.0)
    except Exception as e:
        update_run(run_id, status="error", message=str(e))
