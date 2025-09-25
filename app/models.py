from pydantic import BaseModel
from datetime import datetime

class RunRequest(BaseModel):
    slate_id: str
    n_sims: int = 1000
    pool_size: int = 50
    salary_cap: int = 40000
    min_stack: int = 0         # NEW: hitters from same team
    avoid_hvp: bool = False    # NEW: stub (needs matchups later)

class RunRecord(BaseModel):
    run_id: str
    slate_id: str
    n_sims: int
    created_at: datetime
    status: str = "created"
    progress: float = 0.0
    message: str = ""
