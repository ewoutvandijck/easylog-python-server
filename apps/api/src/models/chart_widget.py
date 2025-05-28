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


class ZLMDataRow(BaseModel):
    """
    Represents one row of data in the chart, typically corresponding to an x-axis category.
    It holds the x-value and a dictionary of all its y-values, where each y-value
    is a ChartDataPointValue (containing the actual value and its color).
    """

    x_value: str = Field(..., description="The value for the x-axis category for this row.")
    y_old: float | None = Field(default=None, description="The old value for this row.")
    y_current: float = Field(..., description="The current value for this row.")
    y_label: str = Field(..., description="The label for the y-axis.")


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
    type: Literal["bar", "line", "pie", "donut", "balloon"] = Field(..., description="The type of chart to render")
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

    @classmethod
    def create_balloon_chart(
        cls,
        title: str,
        data: list[ZLMDataRow] | list[dict[str, Any]],
        description: str | None = None,
    ) -> "ChartWidget":
        """
        Create a balloon chart for ZLM data.
        Colors are based on ZLM score ranges (0-10):
        - 8-10: success
        - 6-7.99: neutral
        - <6: warning
        - Old values: muted

        Args:
            data: Can be either a list of ZLMDataRow objects or a list of dictionaries
                  with keys: x_value, y_current, y_old (optional), y_label.
                  Dictionaries are automatically converted to ZLMDataRow objects.
        """
        # Custom color role map for ZLM charts
        ZLM_CUSTOM_COLOR_ROLE_MAP: dict[str, str] = {
            "success": DEFAULT_COLOR_ROLE_MAP["success"],
            "neutral": "#ffdaaf",  # Pastel orange
            "warning": DEFAULT_COLOR_ROLE_MAP["warning"],
            "old": DEFAULT_COLOR_ROLE_MAP["muted"],
        }

        # Define Literal constants for dictionary keys derived from ZLMDataRow field names
        # This helps ensure consistency if ZLMDataRow fields are refactored.
        # MyPy will check direct attribute access (zlm_row.y_current).
        # These constants make the string key usage more explicit and robust.
        y_current_key = "y_current"
        y_old_key = "y_old"

        processed_data_rows: list[ChartDataRow] = []
        series_configs: list[SeriesConfig] = []

        # Convert dictionaries to ZLMDataRow objects if needed
        zlm_data_rows: list[ZLMDataRow] = []
        if data and isinstance(data[0], dict):
            # Handle dictionary input from LLM - convert to ZLMDataRow objects
            dict_data = cast(list[dict[str, Any]], data)
            for item in dict_data:
                zlm_data_rows.append(
                    ZLMDataRow(
                        x_value=item["x_value"],
                        y_current=item["y_current"],
                        y_old=item.get("y_old"),
                        y_label=item["y_label"],
                    )
                )
        else:
            # Data is already ZLMDataRow objects
            zlm_data_rows = cast(list[ZLMDataRow], data)

        y_axis_label_from_data = zlm_data_rows[0].y_label if zlm_data_rows else "Score"

        has_old_values = False

        for zlm_row in zlm_data_rows:
            current_y = zlm_row.y_current
            current_color_role: str
            if 8 <= current_y <= 10:
                current_color_role = "success"
            elif 6 <= current_y < 8:
                current_color_role = "neutral"
            else:  # current_y < 6
                current_color_role = "warning"

            current_color_hex = ZLM_CUSTOM_COLOR_ROLE_MAP[current_color_role]

            y_values_map: dict[str, ChartDataPointValue] = {
                y_current_key: ChartDataPointValue(value=current_y, color=current_color_hex)
            }

            if zlm_row.y_old is not None:
                has_old_values = True
                old_color_hex = ZLM_CUSTOM_COLOR_ROLE_MAP["old"]
                y_values_map[y_old_key] = ChartDataPointValue(value=zlm_row.y_old, color=old_color_hex)

            processed_data_rows.append(ChartDataRow(x_value=zlm_row.x_value, y_values=y_values_map))

        # Configure series
        label_for_current_series = y_axis_label_from_data.split("(")[0].strip()

        # Use a color from the default palette for the legend item of the current series
        current_series_legend_color = (
            DEFAULT_SERIES_COLORS_PALETTE[0] if DEFAULT_SERIES_COLORS_PALETTE else DEFAULT_FALLBACK_COLOR
        )
        series_configs.append(
            SeriesConfig(
                label=label_for_current_series,
                data_key=y_current_key,
                style=StyleConfig(color=current_series_legend_color),
            )
        )

        if has_old_values:
            label_for_old_series = f"Previous {label_for_current_series}"
            series_configs.append(
                SeriesConfig(
                    label=label_for_old_series,
                    data_key=y_old_key,
                    style=StyleConfig(color=ZLM_CUSTOM_COLOR_ROLE_MAP["old"]),  # Muted color for legend
                )
            )

        y_axis_config = AxisConfig(label=y_axis_label_from_data, domain_min=0, domain_max=10, tick_line=True, show=True)
        x_axis_config = AxisConfig(tick_line=True, show=True)  # Basic X-axis

        return cls(
            type="balloon",
            title=title,
            description=description,
            data=processed_data_rows,
            series=series_configs,
            x_axis=x_axis_config,
            y_axis=y_axis_config,
            legend=True,
            height=400,
            tooltip=TooltipConfig(show=True),
        )

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
        y_axis_config = AxisConfig(tick_line=True, domain_min=y_axis_domain_min, domain_max=y_axis_domain_max)

        return cls(
            type="bar",
            title=title,
            description=description,
            data=processed_data_rows,
            series=series_configs,
            height=height,
            x_axis=AxisConfig(label=x_key, tick_line=True),
            y_axis=y_axis_config,
            horizontal_lines=horizontal_lines,
            tooltip=TooltipConfig(show=True),
            legend=True,
        )

    @classmethod
    def create_line_chart(
        cls,
        title: str,
        data: list[dict[str, Any]],
        x_key: str,
        y_keys: list[str],
        y_labels: list[str] | None = None,
        description: str | None = None,
        height: int = 400,
        horizontal_lines: list[Line] | None = None,
        custom_series_colors_palette: list[str] | None = None,
        y_axis_domain_min: float | None = None,
        y_axis_domain_max: float | None = None,
    ) -> "ChartWidget":
        """
        Create a line chart. Data points for y_keys should be direct numerical values.
        `custom_series_colors_palette` affects line colors.
        """
        if y_labels is None:
            y_labels = y_keys

        if len(y_keys) != len(y_labels):
            raise ValueError("y_keys and y_labels must have the same length for line chart")

        active_series_colors_palette = (
            custom_series_colors_palette if custom_series_colors_palette is not None else DEFAULT_SERIES_COLORS_PALETTE
        )
        if not active_series_colors_palette:
            active_series_colors_palette = [DEFAULT_FALLBACK_COLOR]

        series_hex_colors: dict[str, str] = {}  # Renamed for clarity, this is for line series colors
        for i, y_key_for_default in enumerate(y_keys):
            series_hex_colors[y_key_for_default] = active_series_colors_palette[i % len(active_series_colors_palette)]

        processed_data_rows: list[ChartDataRow] = []
        for raw_item_idx, raw_item in enumerate(data):
            if x_key not in raw_item:
                raise ValueError(
                    f"x_key '{x_key}' not found in line chart data item at index {raw_item_idx}: {raw_item}"
                )

            current_x_value = str(raw_item[x_key])  # Ensure x_value is string
            current_y_values: dict[str, ChartDataPointValue] = {}

            for y_key in y_keys:
                point_value_final: Any
                # The color of the data point (and its marker) will be the series color
                point_color_hex_final: str = series_hex_colors.get(y_key, DEFAULT_FALLBACK_COLOR)

                if y_key not in raw_item:
                    point_value_final = None
                else:
                    # Data for y_key is now expected to be the value directly
                    value_from_data = raw_item[y_key]
                    if not isinstance(value_from_data, (int, float, str)) and value_from_data is not None:
                        # Allow string if it can be cast to float, or None
                        try:
                            if isinstance(value_from_data, str):
                                point_value_final = float(value_from_data)
                            else:  # Should be int or float
                                point_value_final = value_from_data
                        except ValueError:
                            raise ValueError(
                                f"Data for y_key '{y_key}' in x_value '{current_x_value}' (line chart, index {raw_item_idx}) "
                                f"must be a number or None. Received: {value_from_data}"
                            )
                    elif value_from_data is None:
                        point_value_final = None
                    else:  # Is already a number
                        point_value_final = value_from_data

                current_y_values[y_key] = ChartDataPointValue(value=point_value_final, color=point_color_hex_final)

            processed_data_rows.append(ChartDataRow(x_value=current_x_value, y_values=current_y_values))

        series_configs = []
        for i, y_key in enumerate(y_keys):
            line_color = series_hex_colors.get(y_key, DEFAULT_FALLBACK_COLOR)
            style = StyleConfig(
                color=line_color,  # Line color
                stroke_width=2,  # Default stroke width for lines
                radius=4,  # Default radius for markers on lines (markers will also be line_color)
            )
            series_configs.append(SeriesConfig(label=y_labels[i], data_key=y_key, style=style))

        y_axis_config = AxisConfig(
            tick_line=True,
            domain_min=y_axis_domain_min,
            domain_max=y_axis_domain_max,
        )
        x_axis_config = AxisConfig(
            label=x_key,
            tick_line=True,
        )

        return cls(
            type="line",
            title=title,
            description=description,
            data=processed_data_rows,
            series=series_configs,
            height=height,
            x_axis=x_axis_config,
            y_axis=y_axis_config,
            horizontal_lines=horizontal_lines,
            tooltip=TooltipConfig(show=True),
            legend=True,
            animation=True,  # Animation is often nice for line charts
        )
