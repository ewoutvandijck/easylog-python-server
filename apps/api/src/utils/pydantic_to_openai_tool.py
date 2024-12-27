from typing import Type, cast

from openai.types.chat import chat_completion_tool_param
from pydantic import BaseModel


def pydantic_to_openai_tool(
    pydantic_model: Type[BaseModel],
) -> chat_completion_tool_param.ChatCompletionToolParam:
    if pydantic_model.__doc__ is None:
        raise ValueError(
            f"Model {pydantic_model.__name__} is missing a docstring. This is used as the description for the OpenAI tool. Please add a docstring to the model class."
        )

    openai_func_dict = {
        "type": "function",
        "function": {
            "name": pydantic_model.__name__,
            "description": pydantic_model.__doc__,
            "parameters": pydantic_model.model_json_schema(),
        },
    }

    del openai_func_dict["function"]["parameters"]["title"]

    return cast(chat_completion_tool_param.ChatCompletionToolParam, openai_func_dict)
