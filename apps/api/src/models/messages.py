from typing import Literal

from pydantic import BaseModel, Field

MessageRole = Literal["assistant", "user", "system", "developer", "tool"]


class BaseContent(BaseModel):
    id: str = Field(..., description="The ID of the content.")


class TextContent(BaseContent):
    type: Literal["text"] = Field(default="text")

    text: str = Field(..., description="The content of the message.")


class TextDeltaContent(BaseContent):
    type: Literal["text_delta"] = Field(default="text_delta")

    delta: str = Field(..., description="The delta of the content.")


class ToolUseContent(BaseContent):
    type: Literal["tool_use"] = Field(default="tool_use")

    tool_use_id: str = Field(..., description="The ID of the tool use.")

    name: str = Field(..., description="The name of the tool.")

    input: dict = Field(..., description="The arguments of the tool.")


class ToolResultContent(BaseContent):
    type: Literal["tool_result"] = Field(default="tool_result")

    tool_use_id: str = Field(..., description="The ID of the tool use.")

    widget_type: Literal["image", "chart"] | None = Field(default=None, description="The type of the widget.")

    output: str = Field(..., description="The result of the tool.")

    is_error: bool = Field(default=False, description="Whether the tool result is an error.")


class ImageContent(BaseContent):
    type: Literal["image"] = Field(default="image")

    image_url: str = Field(..., description="The URL of the image.")


class FileContent(BaseContent):
    type: Literal["file"] = Field(default="file")

    file_data: str = Field(..., description="The file data of the message.")

    file_name: str = Field(..., description="The name of the file.")


# TODO: Add annotation content
# class AnnotationContent(BaseContent):
#     type: Literal["annotation"] = Field(default="annotation")

#     annotation_type: Literal["url_citation"]

#     url: str = Field(..., description="The URL of the annotation.")

#     title: str = Field(..., description="The title of the annotation.")

#     start_index: int = Field(..., description="The start index of the annotation.")

#     end_index: int = Field(..., description="The end index of the annotation.")


MessageContent = MessageContent = (
    TextContent | ToolUseContent | ToolResultContent | ImageContent | FileContent | TextDeltaContent
)


class Message(BaseModel):
    id: str

    role: MessageRole

    name: str | None = None

    tool_use_id: str | None = None

    content: list[MessageContent]
