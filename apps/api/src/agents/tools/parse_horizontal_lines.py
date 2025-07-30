from typing import Any

from src.models.chart_widget import Line


def parse_horizontal_lines(normalised_lines: list[dict[str, Any]]):
    parsed_horizontal_lines = []
    for i, line_dict in enumerate(normalised_lines):
        if not isinstance(line_dict, dict):
            raise ValueError(
                f"horizontal_lines[{i}] must be a dictionary after parsing, got {type(line_dict)}"
            )

        if "value" not in line_dict:
            raise ValueError(f"horizontal_lines[{i}] missing required 'value' field")

        try:
            value = float(line_dict["value"])
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"horizontal_lines[{i}] 'value' must be numeric, got {line_dict['value']}"
            ) from e

        label = line_dict.get("label")
        color = line_dict.get("color")

        # Validate color format if provided
        if color is not None and not isinstance(color, str):
            raise ValueError(
                f"horizontal_lines[{i}] 'color' must be a string, got {type(color)}"
            )
        parsed_horizontal_lines.append(Line(value=value, label=label, color=color))

    return parsed_horizontal_lines
