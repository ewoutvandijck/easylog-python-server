from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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


ContentType = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]


class ToolResultContent(BaseModel):
    type: Literal["tool_result"] = Field(default="tool_result")

    tool_use_id: str = Field(..., description="The ID of the tool use.")

    content: str = Field(..., description="The result of the tool.")

    content_format: Literal["image", "unknown"] = Field(default="unknown", description="The format of the content.")

    is_error: bool = Field(default=False, description="Whether the tool result is an error.")


class ImageContent(BaseModel):
    type: Literal["image"] = Field(default="image")

    content: str = Field(
        ...,
        description="The raw base64 encoded image data, without any prefixes like `data:image/jpeg;base64,` for example: `iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==`",
    )

    content_type: ContentType = Field(
        default="image/jpeg",
        description="The content type of the image, must start with `image/`",
    )


class PDFContent(BaseModel):
    type: Literal["pdf"] = Field(default="pdf")

    content: str = Field(
        ...,
        description="The base64 encoded PDF data, without any prefixes like `data:application/pdf;base64,`, for example: `iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==`",
    )


MessageContent = TextContent | TextDeltaContent | ToolUseContent | ToolResultContent | ImageContent | PDFContent


class Message(BaseModel):
    role: Literal["assistant", "user", "system", "developer"] = Field(
        default="assistant", description="The role of the message."
    )

    content: list[MessageContent] = Field(..., description="The content of the message.")


class AgentConfig(BaseModel):
    agent_class: str

    model_config = ConfigDict(extra="allow")


class MessageCreateInput(BaseModel):
    content: list[TextContent | ImageContent | PDFContent] = Field(..., description="The content of the message.")

    agent_config: AgentConfig = Field(
        ...,
        description="The configuration for the agent that generated the message. Requires at least a `agent_class` key.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": [
                        {
                            "type": "text",
                            "content": "Hello, what color is this image?",
                        },
                        {
                            "type": "image",
                            "content": "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAE0lEQVR42mP8/5+hngENMNJAEAD4tAx3yVEBjwAAAABJRU5ErkJggg==",
                            "content_type": "image/png",
                        },
                    ],
                    "agent_config": {
                        "agent_class": "OpenAIAssistant",
                        "assistant_id": "asst_5vWL7aefIopE4aU5DcFRmpA5",
                    },
                }
            ]
        }
    }
