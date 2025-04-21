import datetime

from pydantic import BaseModel, Field

from src.models.messages import MessageResponse


class ThreadCreateInput(BaseModel):
    external_id: str | None = Field(
        None,
        description="A unique identifier that can be used to reference this thread. If provided, this external ID can be used instead of the internal ID in all API endpoints. Must be unique across all chats.",
    )


class ThreadResponse(BaseModel):
    id: str
    external_id: str | None
    created_at: datetime.datetime
    updated_at: datetime.datetime
    metadata: dict
    messages: list[MessageResponse]
