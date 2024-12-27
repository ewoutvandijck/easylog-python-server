import inspect
from typing import Any, Callable, cast, get_type_hints

from anthropic.types.tool_param import ToolParam


def function_to_anthropic_tool(
    func: Callable, name: str | None = None, description: str | None = None
) -> ToolParam:
    """
    Converts a Python function to an Anthropic tool specification by inspecting its signature.

    Args:
        func: The Python function to convert

    Returns:
        ToolParam containing the tool specification
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
        json_type = _python_type_to_json_schema(param_type)

        # Add parameter to properties
        parameters["properties"][param_name] = {
            "type": json_type,
            "title": param_name.title(),
        }

        # Add required parameters (those without defaults)
        if param.default == inspect.Parameter.empty:
            parameters["required"].append(param_name)

    # Build tool specification
    tool_spec = {
        "name": name or func.__name__,
        "description": description or func.__doc__ or "",
        "parameters": parameters,
    }

    return cast(ToolParam, tool_spec)


def _python_type_to_json_schema(py_type: type) -> str:
    """
    Convert Python type to JSON Schema type.

    Args:
        py_type: Python type to convert

    Returns:
        Corresponding JSON Schema type as string
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        Any: "string",  # Default to string for Any type
    }
    return type_map.get(py_type, "string")
