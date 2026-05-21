from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    team_name: str


class TeamCreate(TeamBase):
    chat_id: int


class TeamUpdate(BaseModel):
    team_name: str | None = None
    current_checkpoint_id: int | None = None
    score: int | None = None
    status: str | None = None


class TeamResponse(TeamBase):
    chat_id: int
    current_checkpoint_id: int | None = None
    score: int = 0
    status: str = "not_started"
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
