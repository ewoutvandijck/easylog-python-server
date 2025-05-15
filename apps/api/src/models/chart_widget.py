from typing import Any, Literal, cast

from pydantic import BaseModel, Field

# Semantic roles for individual data points
ColorRole = Literal["success", "warning", "neutral", "info", "primary", "accent", "muted"]
DEFAULT_COLOR_ROLE_MAP: dict[str, str] = {
    "success": "#b2f2bb",  # Pastel Green
    "neutral": "#a1c9f4",  # Pastel Blue
    "warning": "#ffb3ba",  # Pastel Red
    "info": "#FFFACD",  # LemonChiffon (Pastel Yellow for informational points)
    "primary": "#DDA0DD",  # Plum (Pastel Purple for primary emphasis)
    "accent": "#B0E0E6",  # PowderBlue (Pastel Cyan/Blue for secondary emphasis)
    "muted": "#D3D3D3",  # LightGray (For de-emphasized points)
}

# Predefined palette for default series colors (used for legends and when colorRole is null)
# Ensure this palette has enough variety or a good fallback strategy.
DEFAULT_SERIES_COLORS_PALETTE: list[str] = [
    "#a1c9f4",  # Pastel Blue
    "#ffdaaf",  # Pastel Orange
    "#c1e1c1",  # Pastel Teal/Mint
    "#d5a6bd",  # Pastel Purple
    "#ffb3ba",  # Pastel Pink
    "#b3dee2",  # Pastel Cyan
]
# Fallback color if the palette is exhausted or for unexpected scenarios
DEFAULT_FALLBACK_COLOR = "#343a40"  # Dark Gray
COLOR_BLACK = "#000000"


class ChartDataPointValue(BaseModel):
    """Represents the structured value for a data point in a y-series, including its color."""

    value: float | str
    color: str = Field(
        ..., description="The HEX color string for this data point (e.g., '#RRGGBB').", pattern=r"^#[0-9a-fA-F]{6}$"
    )


class Line(BaseModel):
    """Represents a line in a chart, including its color. Helpful for things such as goal lines."""

    value: float = Field(..., description="The y-value for this line.")
    label: str | None = Field(default=None, description="The label for this line.")
    color: str | None = Field(
        default=COLOR_BLACK,
        description="The HEX color string for this line (e.g., '#RRGGBB').",
        pattern=r"^#[0-9a-fA-F]{6}$",
    )


class ChartDataRow(BaseModel):
    """
    Represents one row of data in the chart, typically corresponding to an x-axis category.
    It holds the x-value and a dictionary of all its y-values, where each y-value
    is a ChartDataPointValue (containing the actual value and its color).
    """

    x_value: str = Field(..., description="The value for the x-axis category for this row.")
    # The keys of y_values are the data_keys of the y-series (e.g., "sales", "returns").
    y_values: dict[str, ChartDataPointValue] = Field(
        ..., description="A dictionary mapping y-series data_keys to their ChartDataPointValue."
    )


class StyleConfig(BaseModel):
    """Styling configuration for chart elements.

    All properties are optional with sensible defaults.
    """

    color: str | None = None
    fill: str | None = None
    opacity: float | None = Field(default=0.9, ge=0.0, le=1.0)
    stroke_width: int | None = Field(default=2, ge=0, le=10)
    stroke_dasharray: str | None = None
    radius: int | None = Field(default=80, ge=0, le=500)
    inner_radius: int | None = Field(default=40, ge=0, le=500)  # For donut charts


class AxisConfig(BaseModel):
    """Configuration for chart axes.

    Controls visibility and appearance of axes, ticks, and grid lines.
    """

    show: bool = True
    label: str | None = None
    tick_line: bool = True
    tick_margin: int | None = Field(default=10, ge=0, le=100)
    axis_line: bool = True
    grid_lines: bool = False
    formatter: str | None = None  # String template or function name
    domain_min: float | None = Field(default=None, description="Optional minimum value for the axis domain.")
    domain_max: float | None = Field(default=None, description="Optional maximum value for the axis domain.")


class TooltipConfig(BaseModel):
    """Configuration for chart tooltips.

    Controls visibility and content of tooltips when hovering over chart elements.
    """

    show: bool = True
    custom_content: str | None = None  # Template or component name
    hide_label: bool = False


class MarginConfig(BaseModel):
    """Margin configuration for charts.

    Controls the space around the chart within its container.
    """

    top: int = Field(default=20, ge=0, le=100)
    right: int = Field(default=20, ge=0, le=100)
    bottom: int = Field(default=20, ge=0, le=100)
    left: int = Field(default=20, ge=0, le=100)


class SeriesConfig(BaseModel):
    """Configuration for a data series in a chart.

    Controls how a series of data is displayed, including styling and data mapping.
    """

    label: str
    data_key: str
    style: StyleConfig | None = Field(default_factory=StyleConfig)
    stack_id: str | None = None  # For stacked charts
    custom_color: str | None = None


class ChartWidget(BaseModel):
    """Chart configuration.

    Complete configuration for a chart, including data, styling, and behavior.
    """

    # Basic configuration
    type: Literal["bar", "line", "pie", "donut"] = Field(..., description="The type of chart to render")
    title: str = Field(..., description="Chart title")
    description: str | None = Field(default=None, description="Optional chart description")

    # Data configuration
    data: list[ChartDataRow] = Field(
        ...,
        description=(
            "Array of ChartDataRow objects. Each row contains an 'x_value' and "
            "a 'y_values' dictionary mapping series data_keys to ChartDataPointValue objects "
            "(which include the 'value' and its resolved 'color')."
        ),
    )
    series: list[SeriesConfig] = Field(..., description="Configuration for each data series")

    # Axes configuration (not used for pie/donut)
    x_axis: AxisConfig | None = Field(default_factory=AxisConfig, description="X-axis configuration")
    y_axis: AxisConfig | None = Field(default_factory=AxisConfig, description="Y-axis configuration")
    horizontal_lines: list[Line] | None = Field(
        default=None, description="Optional list of horizontal lines to draw on the chart."
    )

    # Visual configuration
    style: StyleConfig | None = Field(default_factory=StyleConfig, description="Global style configuration")
    tooltip: TooltipConfig | None = Field(default_factory=TooltipConfig, description="Tooltip configuration")
    legend: bool = Field(default=True, description="Whether to show the legend")

    # Interaction configuration
    active_index: int | None = Field(default=None, description="Initial active index")
    animation: bool = Field(default=True, description="Whether to animate the chart")

    # Layout configuration
    width: int | None = Field(default=None, description="Optional fixed width in pixels")
    height: int | None = Field(default=400, ge=100, le=2000, description="Chart height in pixels")
    margin: MarginConfig | None = Field(default_factory=MarginConfig, description="Chart margins")

    # # Helper factory methods for common chart types
    # @classmethod
    # def create_pie_chart(
    #     cls,
    #     title: str,
    #     data: list[dict[str, Any]],
    #     name_key: str,
    #     value_key: str,
    #     description: str | None = None,
    #     is_donut: bool = False,
    #     height: int = 400,
    # ) -> "ChartWidget":
    #     """Create a pie or donut chart with minimal configuration.

    #     Args:
    #         title: Chart title
    #         data: List of data objects with name and value properties
    #         name_key: Key in data objects for the segment name
    #         value_key: Key in data objects for the segment value
    #         description: Optional chart description
    #         is_donut: Whether to create a donut chart
    #         height: Chart height in pixels

    #     Example:
    #         ```python
    #         data = [
    #             {"browser": "Chrome", "users": 62},
    #             {"browser": "Safari", "users": 19},
    #             {"browser": "Firefox", "users": 5},
    #             {"browser": "Edge", "users": 4},
    #             {"browser": "Other", "users": 10},
    #         ]

    #         chart = Chart.create_pie_chart(
    #             title="Browser Market Share",
    #             description="Q2 2024 Data",
    #             data=data,
    #             name_key="browser",
    #             value_key="users",
    #             is_donut=True,
    #             height=400,
    #         )
    #         ```

    #     Returns:
    #         Configured Chart instance
    #     """
    #     chart_type = "donut" if is_donut else "pie"

    #     style = StyleConfig(radius=min(height // 3, 150), inner_radius=min(height // 6, 80) if is_donut else 0)

    #     return cls(
    #         type=chart_type,
    #         title=title,
    #         description=description,
    #         data=data,
    #         series=[SeriesConfig(label=name_key, data_key=value_key, style=style)],
    #         height=height,
    #     )

    @classmethod
    def create_bar_chart(
        cls,
        title: str,
        data: list[dict[str, Any]],
        x_key: str,
        y_keys: list[str],
        y_labels: list[str] | None = None,
        description: str | None = None,
        height: int = 400,
        horizontal_lines: list[Line] | None = None,
        custom_color_role_map: dict[str, str] | None = None,
        custom_series_colors_palette: list[str] | None = None,
        y_axis_domain_min: float | None = None,
        y_axis_domain_max: float | None = None,
    ) -> "ChartWidget":
        """
        Create a bar chart. LLM provides data where each y_key value is structured as:
        {"value": <value>, "colorRole": <role_name_str> | null}.
        This factory transforms it into a list of ChartDataRow objects.

        Args:
            data: LLM input. Each y_key's value must be like:
                  {"value": 123, "colorRole": "success"} or {"value": 456, "colorRole": null}.
                  If custom_color_role_map is NOT provided, colorRole (if not null)
                  MUST be one of the defined ColorRole literals (e.g., "success", "info", "primary").
            horizontal_lines: Optional. A list of HorizontalLine objects.
            custom_color_role_map: Optional. A dictionary mapping custom role names (str) to HEX color strings.
                                   If None, DEFAULT_COLOR_ROLE_MAP is used.
            custom_series_colors_palette: Optional. A list of HEX color strings for default series colors.
                                          If None, DEFAULT_SERIES_COLORS_PALETTE is used.
            y_axis_domain_min: Optional. Sets the minimum value for the Y-axis scale.
            y_axis_domain_max: Optional. Sets the maximum value for the Y-axis scale.
        """
        if y_labels is None:
            y_labels = y_keys

        if len(y_keys) != len(y_labels):
            raise ValueError("y_keys and y_labels must have the same length")

        # Determine which color role map and series palette to use
        active_color_role_map = custom_color_role_map if custom_color_role_map is not None else DEFAULT_COLOR_ROLE_MAP

        active_series_colors_palette = (
            custom_series_colors_palette if custom_series_colors_palette is not None else DEFAULT_SERIES_COLORS_PALETTE
        )
        if not active_series_colors_palette:  # Ensure palette is not empty
            active_series_colors_palette = [DEFAULT_FALLBACK_COLOR]

        series_default_hex_colors: dict[str, str] = {}
        # Use the active palette
        palette_to_use = active_series_colors_palette
        for i, y_key_for_default in enumerate(y_keys):
            series_default_hex_colors[y_key_for_default] = palette_to_use[i % len(palette_to_use)]

        processed_data_rows: list[ChartDataRow] = []
        for raw_item_idx, raw_item in enumerate(data):
            if x_key not in raw_item:
                raise ValueError(f"x_key '{x_key}' not found in data item at index {raw_item_idx}: {raw_item}")

            current_x_value = raw_item[x_key]
            current_y_values: dict[str, ChartDataPointValue] = {}

            for y_key in y_keys:
                point_value_final: Any
                point_color_hex_final: str

                if y_key not in raw_item:  # Sparse data for this y_key
                    point_value_final = None
                    point_color_hex_final = series_default_hex_colors.get(y_key, DEFAULT_FALLBACK_COLOR)
                else:
                    value_container = raw_item[y_key]
                    if not (
                        isinstance(value_container, dict)
                        and "value" in value_container
                        and "colorRole" in value_container
                    ):
                        raise ValueError(
                            f"""Data for y_key '{y_key}' in x_value '{current_x_value}' (index {raw_item_idx})
                            is not in the expected format:
                            {{'value': ..., 'colorRole': ...}}. Received: {value_container}"""
                        )

                    point_value_from_container = value_container["value"]
                    role_from_data: str | None = value_container["colorRole"]

                    point_value_final = point_value_from_container
                    if role_from_data is None:
                        point_color_hex_final = series_default_hex_colors.get(y_key, DEFAULT_FALLBACK_COLOR)
                    elif role_from_data in active_color_role_map:
                        # If active_color_role_map is DEFAULT_COLOR_ROLE_MAP (dict[ColorRole, str]),
                        # and role_from_data (str) is in its keys, then role_from_data is a valid ColorRole string.
                        # Pylance might require a cast here if the active_map is strictly typed with ColorRole keys.
                        if active_color_role_map is DEFAULT_COLOR_ROLE_MAP:
                            point_color_hex_final = active_color_role_map[cast(ColorRole, role_from_data)]
                        else:  # active_color_role_map is custom_color_role_map (dict[str, str])
                            point_color_hex_final = active_color_role_map[role_from_data]
                    else:
                        # Behavior if role_from_data is not in active_color_role_map:
                        # If a custom_map was provided but the role isn't in it, it's an issue.
                        # If default_map was used and role isn't a defined ColorRole, it's an issue.
                        raise ValueError(
                            f"Invalid colorRole '{role_from_data}' for y_key '{y_key}' "
                            f"in x_value '{current_x_value}' (index {raw_item_idx}). "
                            f"It's not defined in the active color_role_map. "
                            f"Available in default map: {list(DEFAULT_COLOR_ROLE_MAP.keys())}. "
                            f"If using custom map, ensure role is defined there."
                        )

                current_y_values[y_key] = ChartDataPointValue(value=point_value_final, color=point_color_hex_final)

            processed_data_rows.append(ChartDataRow(x_value=current_x_value, y_values=current_y_values))

        series_configs = []
        for i, y_key in enumerate(y_keys):
            # The style.color for SeriesConfig is for the legend and general series representation
            # It uses the predetermined series default color from the palette
            style = StyleConfig(
                radius=16,  # Default radius for bars
                color=series_default_hex_colors.get(y_key, DEFAULT_FALLBACK_COLOR),
            )
            series_configs.append(SeriesConfig(label=y_labels[i], data_key=y_key, style=style))

        # Configure Y-axis with optional domain settings
        y_axis_config = AxisConfig(
            grid_lines=True, tick_line=True, domain_min=y_axis_domain_min, domain_max=y_axis_domain_max
        )

        return cls(
            type="bar",
            title=title,
            description=description,
            data=processed_data_rows,
            series=series_configs,
            height=height,
            x_axis=AxisConfig(label=x_key, grid_lines=True, tick_line=True),
            y_axis=y_axis_config,
            horizontal_lines=horizontal_lines,
            tooltip=TooltipConfig(show=True),
            legend=True,
        )

    # @classmethod
    # def create_line_chart(
    #     cls,
    #     title: str,
    #     data: list[dict[str, Any]],
    #     x_key: str,
    #     y_keys: list[str],
    #     y_labels: list[str] | None = None,
    #     description: str | None = None,
    #     height: int = 400,
    #     colors: list[str] | None = None,
    # ) -> "ChartWidget":
    #     """Create a line chart with minimal configuration.

    #     Args:
    #         title: Chart title
    #         data: List of data objects
    #         x_key: Key in data objects for the x-axis
    #         y_keys: Keys in data objects for the y-axis values
    #         y_labels: Optional labels for y-axis values (defaults to y_keys)
    #         description: Optional chart description
    #         height: Chart height in pixels
    #         colors: Optional list of colors for each line

    #     Example:
    #         ```python
    #         # Simple line chart with a single data series
    #         data = [
    #             {"date": "2024-01", "temperature": 5},
    #             {"date": "2024-02", "temperature": 7},
    #             {"date": "2024-03", "temperature": 12},
    #             {"date": "2024-04", "temperature": 16},
    #             {"date": "2024-05", "temperature": 20},
    #         ]

    #         chart = Chart.create_line_chart(
    #             title="Temperature Trend",
    #             description="First half of 2024",
    #             data=data,
    #             x_key="date",
    #             y_keys=["temperature"],
    #             height=400,
    #         )

    #         # Line chart with multiple data series and custom colors
    #         data = [
    #             {"month": "Jan", "min_temp": 2, "max_temp": 8},
    #             {"month": "Feb", "min_temp": 3, "max_temp": 10},
    #             {"month": "Mar", "min_temp": 6, "max_temp": 14},
    #             {"month": "Apr", "min_temp": 9, "max_temp": 18},
    #             {"month": "May", "min_temp": 12, "max_temp": 22},
    #         ]

    #         chart = Chart.create_line_chart(
    #             title="Temperature Range",
    #             data=data,
    #             x_key="month",
    #             y_keys=["min_temp", "max_temp"],
    #             y_labels=["Minimum", "Maximum"],
    #             colors=["#0000FF", "#FF0000"],  # Blue for min, red for max
    #         )
    #         ```

    #     Returns:
    #         Configured Chart instance
    #     """
    #     if y_labels is None:
    #         y_labels = y_keys

    #     if len(y_keys) != len(y_labels):
    #         raise ValueError("y_keys and y_labels must have the same length")

    #     # First series will represent the x-axis data
    #     series = [SeriesConfig(label=x_key, data_key=x_key)]

    #     # Add y-series
    #     for i, y_key in enumerate(y_keys):
    #         style = StyleConfig(stroke_width=2, opacity=0.9, radius=4)

    #         # Add color if provided
    #         if colors and i < len(colors):
    #             style.color = colors[i]

    #         series.append(SeriesConfig(label=y_labels[i], data_key=y_key, style=style))

    #     return cls(
    #         type="line",
    #         title=title,
    #         description=description,
    #         data=data,
    #         series=series,
    #         height=height,
    #         x_axis=AxisConfig(label=x_key, grid_lines=False, tick_line=True),
    #         y_axis=AxisConfig(grid_lines=False, tick_line=True),
    #     )
