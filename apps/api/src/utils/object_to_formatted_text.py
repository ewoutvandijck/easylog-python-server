from typing import Any


def object_to_formatted_text(obj: Any, indent_level: int = 0, max_length: int = 1500) -> str:
    """
    Convert an object to a formatted markdown text string.

    Args:
        obj (Any): The object to convert.
        indent_level (int): Current indentation level (used recursively).
        max_length (int): Maximum length of the returned string. If the formatted text exceeds
                         this length, it will be truncated with an ellipsis.

    Returns:
        str: The formatted markdown text string.

    Examples:
        >>> object_to_formatted_text({"a": 1, "b": 2})
        "a → 1
        b → 2"

        >>> object_to_formatted_text([1, 2, 3])
        "- 1
        - 2
        - 3"

        >>> object_to_formatted_text("Hello, world!")
        "Hello, world!"
    """
    # Track the total length to enforce max_length
    total_length = [0]
    truncated = [False]

    def format_with_length_check(obj: Any, indent_level: int = 0) -> str:
        if truncated[0]:
            return ""

        indent = "    " * indent_level

        if isinstance(obj, dict):
            if not obj:
                return ""

            lines = []
            for k, v in obj.items():
                if truncated[0]:
                    break

                if isinstance(v, (dict, list)) and v:
                    key_text = f"{indent}{k}"
                    if total_length[0] + len(key_text) + 1 > max_length:  # +1 for newline
                        truncated[0] = True
                        lines.append(f"{key_text}...")
                        break
                    lines.append(key_text)
                    total_length[0] += len(key_text) + 1  # +1 for newline

                    value_text = format_with_length_check(v, indent_level + 1)
                    if value_text:
                        lines.append(value_text)
                else:
                    formatted_value = format_with_length_check(v, 0)
                    line = f"{indent}{k} → {formatted_value}"
                    if total_length[0] + len(line) + 1 > max_length:  # +1 for newline
                        truncated[0] = True
                        lines.append(f"{indent}{k} → ...")
                        break
                    lines.append(line)
                    total_length[0] += len(line) + 1  # +1 for newline

            return "\n".join(lines)

        elif isinstance(obj, list):
            if not obj:
                return ""

            lines = []
            for item in obj:
                if truncated[0]:
                    break

                if isinstance(item, (dict, list)) and item:
                    list_marker = f"{indent}- "
                    if total_length[0] + len(list_marker) > max_length:
                        truncated[0] = True
                        lines.append(f"{list_marker}...")
                        break
                    lines.append(list_marker)
                    total_length[0] += len(list_marker)

                    # For nested lists, we need consistent indentation with two spaces after the dash
                    if isinstance(item, list):
                        # Use a consistent 2-space indentation after the dash for nested lists
                        nested_indent = indent_level + 1
                        item_text = format_with_length_check(item, nested_indent)
                        if not item_text and truncated[0]:
                            lines.append("...")
                            break

                        # Replace all indentations in the nested list to be consistent
                        item_lines = item_text.split("\n")
                        adjusted_lines = []
                        for line in item_lines:
                            # Remove all indentation and add back the correct amount
                            stripped = line.lstrip()
                            adjusted_line = f"{indent}  {stripped}"
                            if total_length[0] + len(adjusted_line) + 1 > max_length:
                                truncated[0] = True
                                adjusted_lines.append("...")
                                break
                            adjusted_lines.append(adjusted_line)
                            total_length[0] += len(adjusted_line) + 1  # +1 for newline
                        lines.append("\n".join(adjusted_lines))
                    else:
                        # For dictionaries, use the normal indentation
                        item_text = format_with_length_check(item, indent_level + 1)
                        if not item_text and truncated[0]:
                            lines.append("...")
                            break

                        # Remove the first level of indentation from the item text
                        if item_text:
                            item_text = item_text.replace("    " * (indent_level + 1), "    " * indent_level + "  ", 1)
                            lines.append(item_text)
                else:
                    formatted_item = format_with_length_check(item, 0)
                    line = f"{indent}- {formatted_item}"
                    if total_length[0] + len(line) + 1 > max_length:  # +1 for newline
                        truncated[0] = True
                        lines.append(f"{indent}- ...")
                        break
                    lines.append(line)
                    total_length[0] += len(line) + 1  # +1 for newline

            return "\n".join(lines)

        else:
            result = str(obj)
            total_length[0] += len(result)
            if total_length[0] > max_length:
                truncated[0] = True
                # Calculate how much of the string we can include
                available_space = max(0, max_length - (total_length[0] - len(result)) - 3)  # -3 for "..."
                return result[:available_space] + "..." if available_space > 0 else "..."
            return result

    # Start the recursive formatting with length tracking
    result = format_with_length_check(obj, indent_level)

    # If we've truncated but the final result is still under max_length,
    # add an ellipsis to indicate truncation
    if truncated[0] and len(result) < max_length:
        result += "\n..."

    return result
