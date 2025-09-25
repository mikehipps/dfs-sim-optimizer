from pydantic import BaseModel
from datetime import datetime

class RunRequest(BaseModel):
    slate_id: str
    n_sims: int = 1000
    pool_size: int = 50  # NEW: desired lineup-pool size

class RunRecord(BaseModel):
    run_id: str
    slate_id: str
    n_sims: int
    created_at: datetime
    status: str = "created"
    progress: float = 0.0
    message: str = ""
