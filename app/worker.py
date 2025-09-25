import time
from .storage import update_run

def simulate_run(run_id: str, n_steps: int = 20, delay_s: float = 0.1) -> None:
    # mark running
    update_run(run_id, status="running", message="starting simulation", progress=0.0)
    try:
        for step in range(1, n_steps + 1):
            # pretend work happens here (later: real sim kernel)
            time.sleep(delay_s)
            progress = step / n_steps
            update_run(run_id, progress=progress, message=f"step {step}/{n_steps}")
        update_run(run_id, status="done", message="finished", progress=1.0)
    except Exception as e:
        update_run(run_id, status="error", message=str(e))
