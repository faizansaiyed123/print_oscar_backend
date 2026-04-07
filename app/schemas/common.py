from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str


class ActionResponse(MessageResponse):
    success: bool = True


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int


class IdResponse(BaseModel):
    id: int


class TimestampedSchema(ORMModel):
    created_at: datetime
    updated_at: datetime
