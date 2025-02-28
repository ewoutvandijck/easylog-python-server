from typing import Any


def object_to_formatted_text(obj: Any, indent_level: int = 0) -> str:
    """
    Convert an object to a formatted markdown text string.

    Args:
        obj (Any): The object to convert.
        indent_level (int): Current indentation level (used recursively).

    Returns:
        str: The formatted markdown text string.

    Examples:
        >>> object_to_formatted_text({"a": 1, "b": 2})
        "a: 1
        b: 2"

        >>> object_to_formatted_text([1, 2, 3])
        "- 1
        - 2
        - 3"

        >>> object_to_formatted_text("Hello, world!")
        "Hello, world!"
    """
    indent = "    " * indent_level

    if isinstance(obj, dict):
        if not obj:
            return ""

        lines = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)) and v:
                lines.append(f"{indent}{k}:")
                lines.append(object_to_formatted_text(v, indent_level + 1))
            else:
                formatted_value = object_to_formatted_text(v, 0)
                lines.append(f"{indent}{k}: {formatted_value}")

        return "\n".join(lines)

    elif isinstance(obj, list):
        if not obj:
            return ""

        lines = []
        for item in obj:
            if isinstance(item, (dict, list)) and item:
                lines.append(f"{indent}- ")
                # For nested lists, we need consistent indentation with two spaces after the dash
                if isinstance(item, list):
                    # Use a consistent 2-space indentation after the dash for nested lists
                    nested_indent = indent_level + 1
                    item_text = object_to_formatted_text(item, nested_indent)
                    # Replace all indentations in the nested list to be consistent
                    item_lines = item_text.split("\n")
                    adjusted_lines = []
                    for line in item_lines:
                        # Remove all indentation and add back the correct amount
                        stripped = line.lstrip()
                        if stripped.startswith("- "):
                            adjusted_lines.append(f"{indent}  {stripped}")
                        else:
                            adjusted_lines.append(f"{indent}  {stripped}")
                    lines.append("\n".join(adjusted_lines))
                else:
                    # For dictionaries, use the normal indentation
                    item_text = object_to_formatted_text(item, indent_level + 1)
                    # Remove the first level of indentation from the item text
                    item_text = item_text.replace("    " * (indent_level + 1), "    " * indent_level + "  ", 1)
                    lines.append(item_text)
            else:
                formatted_item = object_to_formatted_text(item, 0)
                lines.append(f"{indent}- {formatted_item}")

        return "\n".join(lines)

    else:
        return str(obj)
