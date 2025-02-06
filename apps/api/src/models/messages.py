from typing import List, Literal, Sequence

from pydantic import BaseModel, Field, field_validator


class TextDeltaContent(BaseModel):
    type: Literal["text_delta"] = Field(default="text_delta")

    content: str = Field(..., description="The text of the delta.")


class TextContent(BaseModel):
    type: Literal["text"] = Field(default="text")

    content: str = Field(..., description="The content of the message.")


class ToolUseContent(BaseModel):
    type: Literal["tool_use"] = Field(default="tool_use")

    id: str = Field(..., description="The ID of the tool use.")

    name: str = Field(..., description="The name of the tool.")

    input: dict = Field(..., description="The arguments of the tool.")


class ToolResultContent(BaseModel):
    type: Literal["tool_result"] = Field(default="tool_result")

    tool_use_id: str = Field(..., description="The ID of the tool use.")

    content: str = Field(..., description="The result of the tool.")

    is_error: bool = Field(
        default=False, description="Whether the tool result is an error."
    )


ContentType = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]


class ImageContent(BaseModel):
    type: Literal["image"] = Field(default="image")

    content: str = Field(
        ...,
        description="The content of the message, must start with `data:image/`",
    )

    content_type: ContentType = Field(
        default="image/jpeg",
        description="The content type of the image, must start with `image/`",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.startswith("data:image/"):
            raise ValueError("Content must be a valid image URL")
        return v


class PDFContent(BaseModel):
    type: Literal["pdf"] = Field(default="pdf")

    content: str = Field(
        ...,
        description="The content of the message, must start with `data:application/pdf;base64,`",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.startswith("data:application/pdf;base64,"):
            raise ValueError("Content must be a valid PDF URL")
        return v


MessageContent = (
    TextContent
    | TextDeltaContent
    | ToolUseContent
    | ToolResultContent
    | ImageContent
    | PDFContent
)


class Message(BaseModel):
    role: Literal["assistant", "user", "system", "developer"] = Field(
        default="assistant", description="The role of the message."
    )

    content: Sequence[MessageContent] = Field(
        ..., description="The content of the message."
    )


class AgentConfig(BaseModel):
    agent_class: str

    class Config:
        extra = "allow"


class MessageCreateInput(BaseModel):
    content: List[TextContent | ImageContent | PDFContent] = Field(
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
