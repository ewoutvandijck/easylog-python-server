from typing import Type, cast

from anthropic.types.tool_param import ToolParam
from pydantic import BaseModel


def pydantic_to_anthropic_tool(
    pydantic_model: Type[BaseModel],
    description: str = "",
):
    json_schema = dict(
        name=pydantic_model.__name__,
        description=pydantic_model.__doc__ or description,
        input_schema=pydantic_model.model_json_schema(),
    )

    return cast(ToolParam, json_schema)
