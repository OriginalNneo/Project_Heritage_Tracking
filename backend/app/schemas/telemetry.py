from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TelemetryPayload(BaseModel):
    chat_id: int
    user_id: int
    latitude: float
    longitude: float
    timestamp: datetime | None = None


class TelemetryResponse(BaseModel):
    telemetry_id: int
    team_id: int
    user_id: int
    latitude: float
    longitude: float
    timestamp: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
