from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from .messages import Message


class ThreadCreateInput(BaseModel):
    external_id: str | None = Field(
        None,
        description="A unique identifier that can be used to reference this thread. If provided, this external ID can be used instead of the internal ID in all API endpoints. Must be unique across all chats.",
    )


class ThreadResponse(BaseModel):
    id: str
    external_id: str | None
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] | None = None
    messages: list[Message] | None = []
