from pydantic import BaseModel, Field


class ChatCreateInput(BaseModel):
    external_id: str | None = Field(
        None,
        description="A unique identifier that can be used to reference this chat. If provided, this external ID can be used instead of the internal ID in all API endpoints. Must be unique across all chats.",
    )
