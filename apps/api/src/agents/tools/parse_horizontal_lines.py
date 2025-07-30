"""Utility to parse horizontal_lines definitions coming from the LLM.

The agent may supply the *horizontal_lines* argument in a variety of shapes:
1. ``list[dict[str, Any]]`` – already the desired Python structure
2. ``str`` – a JSON or Python-literal encoded object. This can either be:
   - a single dictionary (``{"value": 10, "label": "Goal"}``)
   - a JSON array of dictionaries (``[{...}, {...}]``)

This helper normalises the input and returns a validated
``list[Line]`` ready to be passed into the ``ChartWidget`` factory
methods.

The implementation is shared by multiple agents so that the logic lives
in a single, well-tested location.
"""
from __future__ import annotations

from typing import Any, Union, List, Dict
import ast
import json

from src.models.chart_widget import Line

# Public API ------------------------------------------------------------------

def parse_horizontal_lines(
    horizontal_lines: Union[str, List[Dict[str, Any]]]
) -> List[Line]:
    """Convert *horizontal_lines* to a list of :class:`~src.models.chart_widget.Line`.

    Parameters
    ----------
    horizontal_lines
        Either a list of dictionaries **or** a JSON/Python-literal encoded
        string representing such list. Each dictionary must contain at
        least the key ``"value"`` (numerical) and can optionally include
        ``"label"`` and ``"color"`` (hex string).

    Returns
    -------
    list[Line]
        A list of validated ``Line`` objects.

    Raises
    ------
    ValueError
        If the input cannot be parsed or the dictionaries do not satisfy
        the required schema.
    """

    # ------------------------------------------------------------------
    # Normalise to ``list[dict]``
    # ------------------------------------------------------------------
    normalised: List[Dict[str, Any]] = []

    if isinstance(horizontal_lines, list):
        # The common happy path – iterate and maybe unpack nested strings
        for idx, item in enumerate(horizontal_lines):
            if isinstance(item, dict):
                normalised.append(item)
            elif isinstance(item, str):
                normalised.extend(_str_to_dicts(item))
            else:
                raise ValueError(
                    f"horizontal_lines[{idx}] must be a dict or str, got {type(item)}"
                )
    elif isinstance(horizontal_lines, str):
        normalised.extend(_str_to_dicts(horizontal_lines))
    else:
        raise ValueError(
            "horizontal_lines must be a list[dict], a JSON encoded string, or None"
        )

    # ------------------------------------------------------------------
    # Validate and convert to ``Line`` objects
    # ------------------------------------------------------------------
    parsed: List[Line] = []
    for i, line_dict in enumerate(normalised):
        if not isinstance(line_dict, dict):
            raise ValueError(
                f"horizontal_lines[{i}] must be a dictionary after parsing, got {type(line_dict)}"
            )

        if "value" not in line_dict:
            raise ValueError(f"horizontal_lines[{i}] missing required 'value' field")

        try:
            value = float(line_dict["value"])
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"horizontal_lines[{i}] 'value' must be numeric, got {line_dict['value']}"
            ) from exc

        label = line_dict.get("label")
        color = line_dict.get("color")

        if color is not None and not isinstance(color, str):
            raise ValueError(
                f"horizontal_lines[{i}] 'color' must be a string, got {type(color)}"
            )

        parsed.append(Line(value=value, label=label, color=color))

    return parsed


# Internal helpers -------------------------------------------------------------

def _str_to_dicts(raw: str) -> List[Dict[str, Any]]:
    """Parse *raw* (JSON or Python literal) into a list of dictionaries."""
    raw_s = raw.strip()
    if not raw_s:
        return []

    try:
        obj = json.loads(raw_s)
    except json.JSONDecodeError:
        # Fallback – e.g. single quotes or Python ``True`` literals
        obj = ast.literal_eval(raw_s)

    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        return [obj]

    raise ValueError("horizontal_lines string must decode to a dict or list of dicts")
