from pydantic import BaseModel
from datetime import datetime

class RunRequest(BaseModel):
    slate_id: str
    n_sims: int = 1000         # number of outcome simulations
    pool_size: int = 50        # how many lineups to sample for the pool
    salary_cap: int = 40000    # lineup salary cap
    min_stack: int = 0         # minimum stacked hitters from one team
    avoid_hvp: bool = False    # (placeholder) avoid hitter-vs-pitcher
    field_size: int = 1000     # NEW: size of the sampled “field”
    corr_sigma: float = 1.5    # NEW: team correlation bump sigma

class RunRecord(BaseModel):
    run_id: str
    slate_id: str
    n_sims: int
    created_at: datetime
    status: str = "created"
    progress: float = 0.0
    message: str = ""
