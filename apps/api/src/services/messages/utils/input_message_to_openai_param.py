from collections.abc import Iterable

from openai.types.chat import (
    ChatCompletionContentPartImageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionMessageParam,
)
from openai.types.chat.chat_completion_content_part_param import File

from src.models.message_create import (
    MessageCreateInputFileContent,
    MessageCreateInputImageContent,
    MessageCreateInputTextContent,
)


def input_content_to_openai_param(
    content: Iterable[MessageCreateInputFileContent | MessageCreateInputImageContent | MessageCreateInputTextContent],
) -> ChatCompletionMessageParam:
    return {
        "role": "user",
        "name": "User",
        "content": [
            text_param(content)
            if isinstance(content, MessageCreateInputTextContent)
            else image_param(content)
            if isinstance(content, MessageCreateInputImageContent)
            else file_param(content)
            for content in content
        ],
    }


def text_param(content: MessageCreateInputTextContent) -> ChatCompletionContentPartTextParam:
    return ChatCompletionContentPartTextParam(
        type="text",
        text=content.text,
    )


def image_param(content: MessageCreateInputImageContent) -> ChatCompletionContentPartImageParam:
    return ChatCompletionContentPartImageParam(
        type="image_url",
        image_url={"url": content.image_url, "detail": "auto"},
    )


def file_param(content: MessageCreateInputFileContent) -> File:
    return File(
        type="file",
        file={
            "file_data": content.file_data,
            "filename": content.file_name,
        },
    )
