from datetime import datetime
from typing import Any

from prisma.models import threads
from pydantic import BaseModel, Field

from src.services.messages.utils.db_message_to_message_model import db_message_to_message_model

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


def transform_db_thread_to_response(db_thread: threads) -> ThreadResponse:
    """Converts a Prisma thread object (with included messages/contents) to a ThreadResponse Pydantic model."""
    messages_response: list[Message] = []
    if db_thread.messages:
        messages_response = [db_message_to_message_model(msg) for msg in db_thread.messages if msg.contents is not None]

    return ThreadResponse(
        id=db_thread.id,
        external_id=db_thread.external_id,
        created_at=db_thread.created_at,
        updated_at=db_thread.updated_at,
        # metadata=db_thread.metadata,  # Assumes metadata is directly compatible or None
        messages=messages_response,
    )
