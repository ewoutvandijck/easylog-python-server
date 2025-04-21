import inspect
from collections.abc import Callable
from typing import Any, cast, get_type_hints

from openai.types.chat import ChatCompletionToolParam


def function_to_openai_tool(
    func: Callable, name: str | None = None, description: str | None = None
) -> ChatCompletionToolParam:
    """
    Converts a Python function to an OpenAI tool specification by inspecting its signature.

    Args:
        func: The Python function to convert
        name: Optional custom name for the tool (defaults to function name)
        description: Optional custom description (defaults to function docstring)

    Returns:
        ChatCompletionToolParam containing the tool specification
    """
    # Get function signature
    sig = inspect.signature(func)

    # Get type hints
    type_hints = get_type_hints(func)

    # Build parameters schema
    parameters = {"type": "object", "properties": {}, "required": []}

    for param_name, param in sig.parameters.items():
        # Get parameter type
        param_type = type_hints.get(param_name, Any)

        # Convert Python type to JSON schema type
        json_type_info = _python_type_to_json_schema(param_type)

        # Handle both string types and dictionary schema definitions
        if isinstance(json_type_info, str):
            parameters["properties"][param_name] = {
                "type": json_type_info,
                "title": param_name.title(),
            }
        else:
            # For complex types like arrays, we merge the schema definition
            parameters["properties"][param_name] = {
                **json_type_info,
                "title": param_name.title(),
            }

        # Add required parameters (those without defaults)
        if param.default == inspect.Parameter.empty:
            parameters["required"].append(param_name)

    # Build tool specification
    tool_spec = {
        "type": "function",
        "function": {
            "name": name or func.__name__,
            "description": description or func.__doc__ or "",
            "parameters": parameters,
        },
    }

    return cast(ChatCompletionToolParam, tool_spec)


def _python_type_to_json_schema(py_type: type) -> str | dict:
    """
    Convert Python type to JSON Schema type.

    Args:
        py_type: Python type to convert

    Returns:
        Corresponding JSON Schema type as string or dict for complex types
    """
    # Handle basic types
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        dict: "object",
        Any: "string",  # Default to string for Any type
    }

    # For basic types, return the string type
    if py_type in type_map:
        return type_map[py_type]

    # Handle List type from typing module
    origin = getattr(py_type, "__origin__", None)
    if origin is list or origin is list:
        # For lists, return a more complex schema
        return {
            "type": "array",
            "items": {},  # Could enhance further to specify item types
        }

    # Default fallback
    return "string"
