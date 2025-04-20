import json

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

from src.models.messages import (
    FileContent,
    ImageContent,
    Message,
    TextContent,
    ToolResultContent,
    ToolUseContent,
)


def generated_message_to_openai_param(message: Message) -> ChatCompletionMessageParam:
    if message.role == "user":
        return ChatCompletionUserMessageParam(
            role=message.role,
            name=message.name or "User",
            content=[
                message_content
                for message_content in [
                    text_content_to_openai_param(content)
                    if content.type == "text"
                    else image_content_to_openai_param(content)
                    if content.type == "image"
                    else file_content_to_openai_param(content)
                    if content.type == "file"
                    else None
                    for content in message.content
                ]
                if message_content is not None
            ],
        )
    elif message.role == "assistant":
        message_content = ChatCompletionAssistantMessageParam(
            role=message.role,
            name=message.name or "Assistant",
            content="".join(
                text_content_to_openai_param(content)["text"] for content in message.content if content.type == "text"
            ),
        )

        if any(content.type == "tool_use" for content in message.content):
            message_content["tool_calls"] = [
                tool_use_content_to_openai_param(content) for content in message.content if content.type == "tool_use"
            ]

        return message_content

    elif message.role == "system":
        return ChatCompletionSystemMessageParam(
            role=message.role,
            name=message.name or "System",
            content="".join(
                text_content_to_openai_param(content)["text"] for content in message.content if content.type == "text"
            ),
        )
    elif message.role == "developer":
        return ChatCompletionDeveloperMessageParam(
            role=message.role,
            name=message.name or "Developer",
            content="".join(
                text_content_to_openai_param(content)["text"] for content in message.content if content.type == "text"
            ),
        )
    elif message.role == "tool":
        if not message.tool_use_id:
            raise ValueError("Tool use ID is required")

        return ChatCompletionToolMessageParam(
            role=message.role,
            tool_call_id=message.tool_use_id,
            content="".join(
                tool_result_content_to_openai_param(content)["text"]
                for content in message.content
                if content.type == "tool_result"
            ),
        )

    raise ValueError(f"Unknown message role: {message.role}")


def text_content_to_openai_param(content: TextContent) -> ChatCompletionContentPartTextParam:
    return ChatCompletionContentPartTextParam(
        type=content.type,
        text=content.text,
    )


def image_content_to_openai_param(content: ImageContent) -> ChatCompletionContentPartImageParam:
    return ChatCompletionContentPartImageParam(
        type="image_url",
        image_url={
            "url": content.image_url,
            "detail": "auto",
        },
    )


def file_content_to_openai_param(content: FileContent) -> File:
    return File(
        type="file",
        file={
            "file_data": content.file_data,
            "filename": content.file_name,
        },
    )


def tool_use_content_to_openai_param(content: ToolUseContent) -> ChatCompletionMessageToolCallParam:
    return ChatCompletionMessageToolCallParam(
        id=content.tool_use_id,
        type="function",
        function={
            "name": content.name,
            "arguments": json.dumps(content.input),
        },
    )


def tool_result_content_to_openai_param(content: ToolResultContent) -> ChatCompletionContentPartTextParam:
    return ChatCompletionContentPartTextParam(
        type="text",
        text=content.output,
    )
