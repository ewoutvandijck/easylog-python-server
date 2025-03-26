from enum import Enum
from typing import Any

from pydantic import BaseModel


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"


class StyleConfig(BaseModel):
    color: str | None = None
    fill: str | None = None
    opacity: float | None = None
    stroke_width: int | None = None
    stroke_dasharray: str | None = None
    radius: int | None = None


class AxisConfig(BaseModel):
    show: bool = True
    label: str | None = None
    tick_line: bool = True
    tick_margin: int | None = None
    axis_line: bool = True
    grid_lines: bool = True
    formatter: str | None = None  # Could be a string template or function name


class TooltipConfig(BaseModel):
    show: bool = True
    custom_content: str | None = None  # Template or component name
    hide_label: bool = False


class SeriesConfig(BaseModel):
    label: str
    data_key: str
    style: StyleConfig | None = None
    stack_id: str | None = None  # For stacked charts
    type: ChartType | None = None  # For mixed charts


class Chart(BaseModel):
    type: ChartType
    title: str
    description: str | None = None

    # Data configuration
    data: list[dict[str, Any]]

    # Series configuration
    series: list[SeriesConfig]

    # Axes configuration
    x_axis: AxisConfig | None = None
    y_axis: AxisConfig | None = None

    # Visual configuration
    style: StyleConfig | None = None
    tooltip: TooltipConfig | None = None
    legend: bool = True

    # Interaction configuration
    active_index: int | None = None
    animation: bool = True

    # Layout configuration
    width: int | None = None
    height: int | None = None
    margin: dict[str, int] | None = None

    # Additional custom configuration
    config: dict[str, Any] | None = None
