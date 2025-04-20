from prisma import Base64
from prisma.enums import message_content_type
from prisma.models import message_contents, messages

from src.models.messages import (
    FileContent,
    ImageContent,
    Message,
    TextContent,
    ToolResultContent,
    ToolUseContent,
)


def db_message_to_message_model(message: messages) -> Message:
    if message.contents is None:
        raise ValueError("Message contents are required")

    return Message(
        id=message.id,
        role=message.role.value,
        name=message.name,
        content=[
            message_content
            for message_content in [
                text_param(content)
                if content.type == message_content_type.text
                else image_param(content)
                if content.type == message_content_type.image
                else file_param(content)
                if content.type == message_content_type.file
                else tool_call_param(content)
                if content.type == message_content_type.tool_use
                else tool_result_param(content)
                if content.type == message_content_type.tool_result
                else None
                for content in message.contents
            ]
            if message_content is not None
        ],
    )


def text_param(content: message_contents) -> TextContent:
    if content.type != message_content_type.text:
        raise ValueError("Text is required")

    if content.text is None:
        raise ValueError("Text is required")

    return TextContent(
        id=content.id,
        type="text",
        text=content.text,
    )


def image_param(content: message_contents) -> ImageContent:
    if content.type != message_content_type.image:
        raise ValueError("Image is required")

    if not content.image_url:
        raise ValueError("Image URL is required")

    return ImageContent(
        id=content.id,
        type="image",
        image_url=content.image_url,
    )


def file_param(content: message_contents) -> FileContent:
    if content.type != message_content_type.file:
        raise ValueError("File is required")

    if not content.file_data:
        raise ValueError("File data is required")

    if not content.file_name:
        raise ValueError("File name is required")

    return FileContent(
        id=content.id,
        type="file",
        file_data=Base64.decode(content.file_data).decode("utf-8"),
        file_name=content.file_name,
    )


def tool_call_param(content: message_contents) -> ToolUseContent:
    if content.type != message_content_type.tool_use:
        raise ValueError("Tool use is required")

    if not content.tool_use_id:
        raise ValueError("Tool use ID is required")

    if not content.tool_name:
        raise ValueError("Tool use name is required")

    if not content.tool_input:
        raise ValueError("Tool use arguments are required")

    return ToolUseContent(
        id=content.id,
        tool_use_id=content.tool_use_id,
        type="tool_use",
        name=content.tool_name,
        input=dict(content.tool_input),
    )


def tool_result_param(content: message_contents) -> ToolResultContent:
    if content.type != message_content_type.tool_result:
        raise ValueError("Tool result is required")

    if not content.tool_output:
        raise ValueError("Tool output is required")

    if not content.tool_use_id:
        raise ValueError("Tool use ID is required")

    return ToolResultContent(
        id=content.id,
        type="tool_result",
        widget_type=content.widget_type.value if content.widget_type else None,
        tool_use_id=content.tool_use_id,
        output=content.tool_output,
    )
