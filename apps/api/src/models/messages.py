from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.models.charts import Chart

MessageRole = Literal["assistant", "user", "system", "developer", "tool"]


class BaseContent(BaseModel):
    id: str = Field(..., description="The ID of the content.")

    role: MessageRole = Field(..., description="The role of the content.")

    created_at: datetime = Field(..., description="The creation date of the content.")


class TextContent(BaseContent):
    type: Literal["text"] = Field(default="text")

    text: str = Field(..., description="The content of the message.")


class TextDeltaContent(BaseContent):
    type: Literal["text_delta"] = Field(default="text_delta")

    content_id: str = Field(..., description="The ID of the content that the delta is for.")

    delta: str = Field(..., description="The delta of the content.")


class ToolUseContent(BaseContent):
    type: Literal["tool_use"] = Field(default="tool_use")

    id: str = Field(..., description="The ID of the tool use.")

    name: str = Field(..., description="The name of the tool.")

    input: dict = Field(..., description="The arguments of the tool.")


class ToolResultContent(BaseContent):
    type: Literal["tool_result"] = Field(default="tool_result")

    tool_use_id: str = Field(..., description="The ID of the tool use.")

    output: str = Field(..., description="The result of the tool.")

    is_error: bool = Field(default=False, description="Whether the tool result is an error.")


class ToolResultDeltaContent(BaseContent):
    type: Literal["tool_result_delta"] = Field(default="tool_result_delta")

    content_id: str = Field(..., description="The ID of the content that the delta is for.")

    delta: str = Field(..., description="The delta of the tool result.")


class ImageWidgetContent(BaseContent):
    type: Literal["tool_result"] = Field(default="tool_result")

    widget_type: Literal["image"] = Field(default="image", description="The type of the widget.")

    image_url: str = Field(..., description="The URL of the image.")

    image_detail: Literal["low", "medium", "high"] = Field(default="low", description="The detail of the image.")


class ChartWidgetContent(BaseContent):
    type: Literal["tool_result"] = Field(default="tool_result")

    widget_type: Literal["chart"] = Field(default="chart", description="The type of the widget.")

    chart_data: Chart = Field(..., description="The data of the chart.")


class ImageContent(BaseContent):
    type: Literal["image"] = Field(default="image")

    image_url: str = Field(..., description="The URL of the image.")


class FileContent(BaseContent):
    type: Literal["pdf"] = Field(default="pdf")

    file_data: str = Field(..., description="The file data of the message.")

    file_name: str = Field(..., description="The name of the file.")


class AnnotationContent(BaseContent):
    type: Literal["annotation"] = Field(default="annotation")

    annotation_type: Literal["url_citation"]

    url: str = Field(..., description="The URL of the annotation.")

    title: str = Field(..., description="The title of the annotation.")

    start_index: int = Field(..., description="The start index of the annotation.")

    end_index: int = Field(..., description="The end index of the annotation.")


MessageContent = (
    TextContent
    | ToolUseContent
    | ToolResultContent
    | ImageContent
    | FileContent
    | AnnotationContent
    | TextDeltaContent
    | ToolResultDeltaContent
)


class GeneratedMessage(BaseModel):
    role: MessageRole

    tool_use_id: str | None = None

    content: list[MessageContent]
