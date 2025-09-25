import time
from .storage import update_run, load_run
from .data_storage import get_inputs_info
from .pool import build_pool, save_pool

def simulate_run(run_id: str, n_steps: int = 20, delay_s: float = 0.1) -> None:
    update_run(run_id, status="running", message="starting simulation", progress=0.0)
    try:
        rec = load_run(run_id)
        if not rec:
            update_run(run_id, status="error", message="run record missing")
            return

        slate_id = rec.get("slate_id", "")
        info = get_inputs_info(slate_id)
        if not info.get("has_projections") or not info.get("has_ownership"):
            update_run(
                run_id,
                status="error",
                message=f"missing inputs for {slate_id} (projections and ownership required)",
                progress=0.0,
            )
            return

        # Build a small lineup pool (stub) and save it as an artifact
        pool = build_pool(slate_id, n_lineups=10)
        save_pool(run_id, pool)

        # Pretend to simulate progress
        for step in range(1, n_steps + 1):
            time.sleep(delay_s)
            update_run(run_id, progress=step / n_steps, message=f"step {step}/{n_steps}")

        update_run(run_id, status="done", message="finished", progress=1.0)
    except Exception as e:
        update_run(run_id, status="error", message=str(e))
