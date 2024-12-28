from typing import List, Literal, Sequence

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    agent_class: str

    class Config:
        extra = "allow"


class BaseMessageContent(BaseModel):
    chunk_index: int = Field(
        default=0, description="The index of the content in the message."
    )


class TextContent(BaseMessageContent):
    # TODO: add support for other content types
    type: Literal["text"] = Field(
        default="text", description="The type of content in the message."
    )

    content: str = Field(..., description="The content of the message.")


class ToolUseContent(BaseMessageContent):
    type: Literal["tool_use"] = Field(
        default="tool_use", description="The type of content in the message."
    )

    id: str = Field(..., description="The ID of the tool use.")

    name: str = Field(..., description="The name of the tool.")

    input: dict = Field(..., description="The arguments of the tool.")


class ToolResultContent(BaseMessageContent):
    type: Literal["tool_result"] = Field(
        default="tool_result", description="The type of content in the message."
    )

    tool_use_id: str = Field(..., description="The ID of the tool use.")

    content: str = Field(..., description="The result of the tool.")

    is_error: bool = Field(
        default=False, description="Whether the tool result is an error."
    )


class Message(BaseModel):
    role: Literal["assistant", "user"] = Field(
        default="assistant", description="The role of the message."
    )

    content: Sequence[TextContent | ToolUseContent | ToolResultContent] = Field(
        ..., description="The content of the message."
    )


class MessageCreateInput(BaseModel):
    content: List[TextContent] = Field(..., description="The content of the message.")

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
