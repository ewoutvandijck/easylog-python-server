from typing import List, Literal

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    agent_class: str

    class Config:
        extra = "allow"


class MessageContent(BaseModel):
    # TODO: add support for other content types
    type: Literal["text"] = Field(
        default="text", description="The type of content in the message."
    )

    index: int = Field(
        default=0, description="The index of the content in the message."
    )

    content: str = Field(..., description="The content of the message.")


class Message(BaseModel):
    role: Literal["assistant", "user"] = Field(
        default="assistant", description="The role of the message."
    )
    content: List[MessageContent] = Field(
        ..., description="The content of the message."
    )


class MessageCreateInput(BaseModel):
    content: List[MessageContent] = Field(
        ..., description="The content of the message."
    )
    agent_config: AgentConfig = Field(
        ...,
        description="The configuration for the agent that generated the message. Requires at least a `agent_class` key.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": [{"type": "text", "content": "Hello, how are you?"}],
                    "agent_config": {
                        "agent_class": "OpenAIAssistant",
                        "assistant_id": "asst_5vWL7aefIopE4aU5DcFRmpA5",
                    },
                }
            ]
        }
    }


class MessageChunkContent(MessageContent):
    chunk_index: int
