from typing import Annotated, Literal

from pydantic import BaseModel, Field

from src.models.chart_widget import ChartWidget as ChartWidgetData

# Import the modified ImageWidget for embedded images
from src.models.image_widget import ImageWidget as EmbeddedImageWidgetData
from src.models.multiple_choice_widget import MultipleChoiceWidget as MultipleChoiceWidgetData

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


# START: Define individual widget data models (now with discriminators)
class TextWidgetData(BaseModel):
    widget_type: Literal["text"] = Field("text", description="Discriminator for text widget.")
    text: str = Field(..., description="The text content for the widget.")


class ImageUrlWidgetData(BaseModel):
    widget_type: Literal["image_url"] = Field("image_url", description="Discriminator for image URL widget.")
    url: str = Field(..., description="The URL of the image.")


WidgetOutput = (
    TextWidgetData | EmbeddedImageWidgetData | ImageUrlWidgetData | ChartWidgetData | MultipleChoiceWidgetData
)


class ToolResultContent(BaseModel):
    type: Literal["tool_result"] = Field(default="tool_result")
    tool_use_id: str = Field(..., description="The ID of the tool use.")
    widget_type: Literal["text", "image", "image_url", "chart", "multiple_choice"] | None = Field(
        default=None, description="The type of the widget. This determines the structure of 'output'."
    )

    output: Annotated[WidgetOutput, Field(discriminator="widget_type")] = Field(
        ...,
        description="The structured output of the tool, corresponding to the widget_type, or a simple string if widget_type is None or for errors.",
    )
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


MessageContent = TextContent | ToolUseContent | ToolResultContent | ImageContent | FileContent | TextDeltaContent


class MessageResponse(BaseModel):
    id: str

    role: MessageRole

    name: str | None = None

    tool_use_id: str | None = None

    content: list[Annotated[MessageContent, Field(discriminator="type")]]
