from openai.types.chat import ChatCompletionMessageParam

from src.models.messages import GeneratedMessage


def generated_message_to_openai_param(message: GeneratedMessage) -> ChatCompletionMessageParam:
    raise NotImplementedError("Not implemented")
