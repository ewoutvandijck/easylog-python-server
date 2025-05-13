from typing import Any, Literal

from pydantic import BaseModel, Field


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


class ChartWidget(BaseModel):
    """Chart configuration.

    Complete configuration for a chart, including data, styling, and behavior.
    """

    # Basic configuration
    type: Literal["bar", "line", "pie", "donut"] = Field(..., description="The type of chart to render")
    title: str = Field(..., description="Chart title")
    description: str | None = Field(default=None, description="Optional chart description")

    # Data configuration
    data: list[dict[str, Any]] = Field(..., description="Array of data objects for the chart")
    series: list[SeriesConfig] = Field(..., description="Configuration for each data series")

    # Axes configuration (not used for pie/donut)
    x_axis: AxisConfig | None = Field(default_factory=AxisConfig, description="X-axis configuration")
    y_axis: AxisConfig | None = Field(default_factory=AxisConfig, description="Y-axis configuration")

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

    # Helper factory methods for common chart types
    @classmethod
    def create_pie_chart(
        cls,
        title: str,
        data: list[dict[str, Any]],
        name_key: str,
        value_key: str,
        description: str | None = None,
        is_donut: bool = False,
        height: int = 400,
    ) -> "ChartWidget":
        """Create a pie or donut chart with minimal configuration.

        Args:
            title: Chart title
            data: List of data objects with name and value properties
            name_key: Key in data objects for the segment name
            value_key: Key in data objects for the segment value
            description: Optional chart description
            is_donut: Whether to create a donut chart
            height: Chart height in pixels

        Example:
            ```python
            data = [
                {"browser": "Chrome", "users": 62},
                {"browser": "Safari", "users": 19},
                {"browser": "Firefox", "users": 5},
                {"browser": "Edge", "users": 4},
                {"browser": "Other", "users": 10},
            ]

            chart = Chart.create_pie_chart(
                title="Browser Market Share",
                description="Q2 2024 Data",
                data=data,
                name_key="browser",
                value_key="users",
                is_donut=True,
                height=400,
            )
            ```

        Returns:
            Configured Chart instance
        """
        chart_type = "donut" if is_donut else "pie"

        style = StyleConfig(radius=min(height // 3, 150), inner_radius=min(height // 6, 80) if is_donut else 0)

        return cls(
            type=chart_type,
            title=title,
            description=description,
            data=data,
            series=[SeriesConfig(label=name_key, data_key=value_key, style=style)],
            height=height,
        )

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
        stacked: bool = False,
        colors: list[str] | None = None,
    ) -> "ChartWidget":
        """Create a bar chart with minimal configuration.

        Args:
            title: Chart title
            data: List of data objects
            x_key: Key in data objects for the x-axis
            y_keys: Keys in data objects for the y-axis values
            y_labels: Optional labels for y-axis values (defaults to y_keys)
            description: Optional chart description
            height: Chart height in pixels
            stacked: Whether bars should be stacked
            colors: Optional list of colors for each bar series

        Example:
            ```python
            # Simple bar chart with one data series
            data = [
                {"month": "Jan", "sales": 120},
                {"month": "Feb", "sales": 150},
                {"month": "Mar", "sales": 180},
                {"month": "Apr", "sales": 170},
                {"month": "May", "sales": 200},
            ]

            chart = Chart.create_bar_chart(
                title="Monthly Sales", description="2024 Sales Data", data=data, x_key="month", y_keys=["sales"], height=400
            )

            # Bar chart with multiple data series and custom colors
            data = [
                {"quarter": "Q1", "product_a": 120, "product_b": 90},
                {"quarter": "Q2", "product_a": 150, "product_b": 110},
                {"quarter": "Q3", "product_a": 180, "product_b": 130},
                {"quarter": "Q4", "product_a": 210, "product_b": 150},
            ]

            chart = Chart.create_bar_chart(
                title="Quarterly Sales by Product",
                data=data,
                x_key="quarter",
                y_keys=["product_a", "product_b"],
                y_labels=["Product A", "Product B"],
                stacked=True,
                colors=["#8884d8", "#82ca9d"],
            )
            ```

        Returns:
            Configured Chart instance
        """
        if y_labels is None:
            y_labels = y_keys

        if len(y_keys) != len(y_labels):
            raise ValueError("y_keys and y_labels must have the same length")

        if colors and len(colors) != len(y_keys):
            raise ValueError("colors list length must match y_keys list length")

        # First series will represent the x-axis categories
        series = [SeriesConfig(label=x_key, data_key=x_key)]

        # Add data series for y values
        for i, y_key in enumerate(y_keys):
            # Initialize style with default radius
            style = StyleConfig(radius=16)

            if colors:
                style.color = colors[i]

            series_config = SeriesConfig(label=y_labels[i], data_key=y_key, style=style)

            # Add stack_id for stacked bar charts
            if stacked:
                series_config.stack_id = "stack1"

            series.append(series_config)

        return cls(
            type="bar",
            title=title,
            description=description,
            data=data,
            series=series,
            height=height,
            x_axis=AxisConfig(label=x_key, grid_lines=False, tick_line=True),
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
        colors: list[str] | None = None,
    ) -> "ChartWidget":
        """Create a line chart with minimal configuration.

        Args:
            title: Chart title
            data: List of data objects
            x_key: Key in data objects for the x-axis
            y_keys: Keys in data objects for the y-axis values
            y_labels: Optional labels for y-axis values (defaults to y_keys)
            description: Optional chart description
            height: Chart height in pixels
            colors: Optional list of colors for each line

        Example:
            ```python
            # Simple line chart with a single data series
            data = [
                {"date": "2024-01", "temperature": 5},
                {"date": "2024-02", "temperature": 7},
                {"date": "2024-03", "temperature": 12},
                {"date": "2024-04", "temperature": 16},
                {"date": "2024-05", "temperature": 20},
            ]

            chart = Chart.create_line_chart(
                title="Temperature Trend",
                description="First half of 2024",
                data=data,
                x_key="date",
                y_keys=["temperature"],
                height=400,
            )

            # Line chart with multiple data series and custom colors
            data = [
                {"month": "Jan", "min_temp": 2, "max_temp": 8},
                {"month": "Feb", "min_temp": 3, "max_temp": 10},
                {"month": "Mar", "min_temp": 6, "max_temp": 14},
                {"month": "Apr", "min_temp": 9, "max_temp": 18},
                {"month": "May", "min_temp": 12, "max_temp": 22},
            ]

            chart = Chart.create_line_chart(
                title="Temperature Range",
                data=data,
                x_key="month",
                y_keys=["min_temp", "max_temp"],
                y_labels=["Minimum", "Maximum"],
                colors=["#0000FF", "#FF0000"],  # Blue for min, red for max
            )
            ```

        Returns:
            Configured Chart instance
        """
        if y_labels is None:
            y_labels = y_keys

        if len(y_keys) != len(y_labels):
            raise ValueError("y_keys and y_labels must have the same length")

        # First series will represent the x-axis data
        series = [SeriesConfig(label=x_key, data_key=x_key)]

        # Add y-series
        for i, y_key in enumerate(y_keys):
            style = StyleConfig(stroke_width=2, opacity=0.9, radius=4)

            # Add color if provided
            if colors and i < len(colors):
                style.color = colors[i]

            series.append(SeriesConfig(label=y_labels[i], data_key=y_key, style=style))

        return cls(
            type="line",
            title=title,
            description=description,
            data=data,
            series=series,
            height=height,
            x_axis=AxisConfig(label=x_key, grid_lines=False, tick_line=True),
            y_axis=AxisConfig(grid_lines=False, tick_line=True),
        )
