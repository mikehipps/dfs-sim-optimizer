from pydantic import BaseModel, Field, conint
from datetime import datetime

class RunRequest(BaseModel):
    slate_id: str = Field(..., min_length=1)
    n_sims: conint(ge=1, le=1_000_000) = 1000

class RunRecord(BaseModel):
    run_id: str
    slate_id: str
    n_sims: int
    created_at: datetime
    status: str = "created"    # created | running | done | error
    progress: float = 0.0      # 0.0 → 1.0
    message: str = ""
