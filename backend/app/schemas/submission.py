from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SubmissionBase(BaseModel):
    team_id: int
    checkpoint_id: int
    submitted_answer: str | None = None


class SubmissionCreate(SubmissionBase):
    submitted_by: int | None = None


class SubmissionResponse(SubmissionBase):
    sub_id: int
    status: str = "pending"
    submitted_by: int | None = None
    timestamp: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
