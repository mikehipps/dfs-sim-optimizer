from pydantic import BaseModel, Field, confloat, conint

class PlayerProjection(BaseModel):
    player_id: str = Field(..., min_length=1)
    name: str
    team: str
    position: str
    salary: conint(ge=0) = 0
    proj: confloat(ge=0)  # projected points

class PlayerOwnership(BaseModel):
    player_id: str
    own_pct: confloat(ge=0, le=100)
