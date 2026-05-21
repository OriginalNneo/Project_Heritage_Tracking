from pydantic import BaseModel, ConfigDict


class CheckpointBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    target_radius: float = 20.0
    riddle_text: str | None = None
    task_description: str | None = None
    answer: str | None = None
    hint: str | None = None
    order_index: int


class CheckpointCreate(CheckpointBase):
    pass


class CheckpointUpdate(BaseModel):
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    target_radius: float | None = None
    riddle_text: str | None = None
    task_description: str | None = None
    answer: str | None = None
    hint: str | None = None
    order_index: int | None = None


class CheckpointResponse(CheckpointBase):
    checkpoint_id: int

    model_config = ConfigDict(from_attributes=True)
