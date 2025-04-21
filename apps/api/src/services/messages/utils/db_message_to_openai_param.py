from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionDeveloperMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_content_part_param import File
from prisma import Base64
from prisma.enums import message_content_type, message_role
from prisma.models import message_contents, messages


def db_message_to_openai_param(message: messages) -> ChatCompletionMessageParam:
    if message.contents is None:
        raise ValueError("Message contents are required")

    if message.role == message_role.user:
        return ChatCompletionUserMessageParam(
            role=message.role.value,
            content=[
                message_content
                for message_content in [
                    text_param(content)
                    if content.type == message_content_type.text
                    else image_param(content)
                    if content.type == message_content_type.image
                    else file_param(content)
                    if content.type == message_content_type.file
                    else None
                    for content in message.contents
                ]
                if message_content is not None
            ],
        )
    elif message.role == message_role.assistant:
        message_content = ChatCompletionAssistantMessageParam(
            role=message.role.value,
            content="".join(
                text_param(content)["text"] for content in message.contents if content.type == message_content_type.text
            ),
        )

        if any(content.type == message_content_type.tool_use for content in message.contents):
            message_content["tool_calls"] = [
                tool_call_param(content)
                for content in message.contents
                if content.type == message_content_type.tool_use
            ]

        return message_content

    elif message.role == message_role.system:
        return ChatCompletionSystemMessageParam(
            role=message.role.value,
            content=[
                message_content
                for message_content in [
                    text_param(content) if content.type == message_content_type.text else None
                    for content in message.contents
                ]
                if message_content is not None
            ],
        )
    elif message.role == message_role.developer:
        return ChatCompletionDeveloperMessageParam(
            role=message.role.value,
            name=message.name or "Developer",
            content=[
                message_content
                for message_content in [
                    text_param(content) if content.type == message_content_type.text else None
                    for content in message.contents
                ]
                if message_content is not None
            ],
        )
    elif message.role == message_role.tool:
        if not message.tool_use_id:
            raise ValueError("Tool use ID is required")

        return ChatCompletionToolMessageParam(
            role="tool",
            tool_call_id=message.tool_use_id,
            content="".join(
                tool_result_param(content)["text"]
                for content in message.contents
                if content.type == message_content_type.tool_result
            ),
        )

    raise ValueError(f"Unsupported message role: {message.role}")


def text_param(content: message_contents) -> ChatCompletionContentPartTextParam:
    if content.type != message_content_type.text:
        raise ValueError("Text is required")

    if content.text is None:
        raise ValueError("Text is required")

    return ChatCompletionContentPartTextParam(
        type="text",
        text=content.text,
    )


def image_param(content: message_contents) -> ChatCompletionContentPartImageParam:
    if content.type != message_content_type.image:
        raise ValueError("Image is required")

    if content.image_url is None:
        raise ValueError("Image URL is required")

    return ChatCompletionContentPartImageParam(
        type="image_url",
        image_url={"url": content.image_url, "detail": "auto"},
    )


def file_param(content: message_contents) -> File:
    if content.type != message_content_type.file:
        raise ValueError("File is required")

    if content.file_data is None:
        raise ValueError("File data is required")

    if content.file_name is None:
        raise ValueError("File name is required")

    return File(
        type="file",
        file={
            "file_data": Base64.decode(content.file_data).decode("utf-8"),
            "filename": content.file_name,
        },
    )


def tool_call_param(content: message_contents) -> ChatCompletionMessageToolCallParam:
    if content.type != message_content_type.tool_use:
        raise ValueError("Tool use is required")

    if content.tool_use_id is None:
        raise ValueError("Tool use ID is required")

    if content.tool_name is None:
        raise ValueError("Tool use name is required")

    if content.tool_input is None:
        raise ValueError("Tool use arguments are required")

    return ChatCompletionMessageToolCallParam(
        id=content.tool_use_id,
        type="function",
        function={
            "name": content.tool_name,
            "arguments": str(content.tool_input),
        },
    )


def tool_result_param(content: message_contents) -> ChatCompletionContentPartTextParam:
    if content.type != message_content_type.tool_result:
        raise ValueError("Tool result is required")

    if content.tool_output is None:
        raise ValueError("Tool output is required")

    return ChatCompletionContentPartTextParam(
        type="text",
        text=content.tool_output,
    )
