from datetime import datetime
from typing import Literal

from pydantic import BaseModel

MessageRole = Literal["developer", "system", "user", "assistant", "tool"]


class ResponseBase(BaseModel):
    id: str
    role: MessageRole
    message_id: str
    created_at: datetime


class ToolUseContent(ResponseBase):
    content_type: Literal["tool_use"]
    tool_use_id: str
    name: str
    arguments: dict


class ToolResultContent(ResponseBase):
    content_type: Literal["tool_result"]
    tool_use_id: str
    name: str
    arguments: dict
    result: str
    is_error: bool


class ImageContent(ResponseBase):
    content_type: Literal["image"]
    image_url: str


class TextContent(ResponseBase):
    content_type: Literal["text"]
    text: str


class TextDeltaContent(ResponseBase):
    content_type: Literal["text_delta"]
    content_id: str
    text: str


class FileContent(ResponseBase):
    content_type: Literal["file"]
    file_name: str
    file_data: bytes


MessageContentResponse = (
    ImageContent | ToolUseContent | ToolResultContent | TextContent | TextDeltaContent | FileContent
)
