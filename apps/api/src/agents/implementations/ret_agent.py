import json
import os
from collections.abc import Callable, Iterable
from glob import glob
from typing import Any

import pandas as pd
from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from src.agents.base_agent import BaseAgent
from src.agents.tools.base_tools import BaseTools
from src.agents.tools.easylog_backend_tools import EasylogBackendTools
from src.agents.tools.easylog_sql_tools import EasylogSqlTools
from src.models.chart_widget import ChartWidget, Line
from src.models.multiple_choice_widget import Choice, MultipleChoiceWidget
from src.settings import settings
from src.utils.function_to_openai_tool import function_to_openai_tool


class RETAgentConfig(BaseModel):
    prompt: str = Field(
        default="You are a helpful assistant.",
        description="The system prompt or persona instructions for this role, defining its behavior and tone.",
    )
    model: str = Field(
        default="openai/gpt-4.1",
        description="The model identifier to use for this role, e.g., 'openai/gpt-4.1' or any model from https://openrouter.ai/models.",
    )


class RETAgent(BaseAgent[RETAgentConfig]):
    def on_init(self) -> None:
        self.sql_tools = EasylogSqlTools(self.request_headers.get("ssh_key_path"))

    def get_tools(self) -> list[Callable]:
        easylog_token = self.request_headers.get("x-easylog-bearer-token", "")
        easylog_backend_tools = EasylogBackendTools(
            bearer_token=easylog_token,
            base_url=settings.EASYLOG_API_URL,
        )

        easylog_sql_tools = EasylogSqlTools(
            ssh_key_path=settings.EASYLOG_SSH_KEY_PATH,
            ssh_host=settings.EASYLOG_SSH_HOST,
            ssh_username=settings.EASYLOG_SSH_USERNAME,
            db_password=settings.EASYLOG_DB_PASSWORD,
            db_user=settings.EASYLOG_DB_USER,
            db_host=settings.EASYLOG_DB_HOST,
            db_port=settings.EASYLOG_DB_PORT,
            db_name=settings.EASYLOG_DB_NAME,
        )

        async def tool_search_documents(search_query: str) -> str:
            """Search for documents in the knowledge database using a semantic search query.

            This tool allows you to search through the knowledge database for relevant documents
            based on a natural language query. The search is performed using semantic matching,
            which means it will find documents that are conceptually related to your query,
            even if they don't contain the exact words.

            Args:
                search_query (str): A natural language query describing what you're looking for.
                                  For example: "information about metro systems" or "how to handle customer complaints"

            Returns:
                str: A formatted string containing the search results, where each result includes:
                     - The document's properties in JSON format
                     - The relevance score indicating how well the document matches the query
            """

            result = await self.search_documents(
                search_query,
                subjects=None,  # Allow all subjects, change this to ["COPD", "Asthma"] to only allow these subjects
            )

            return "\n-".join(
                [
                    f"Path: {document.path} - Summary: {document.summary}"
                    for document in result
                ]
            )

        async def tool_get_document_contents(path: str) -> str:
            """Retrieve the complete contents of a specific document from the knowledge database.

            This tool allows you to access the full content of a document when you need detailed information
            about a specific topic. The document contents are returned in JSON format, making it easy to
            parse and work with the data programmatically.

            Args:
                path (str): The unique path or identifier of the document you want to retrieve.
                          This is typically obtained from the search results of tool_search_documents.

            Returns:
                str: A JSON string containing the complete document contents, including all properties
                     and metadata. The JSON is formatted with proper string serialization for all data types.
            """
            return json.dumps(await self.get_document(path), default=str)

        def tool_ask_multiple_choice(
            question: str, choices: list[dict[str, str]]
        ) -> MultipleChoiceWidget:
            """Asks the user a multiple-choice question with distinct labels and values.
                When using this tool, you must not repeat the same question or answers in text unless asked to do so by the user.
                This widget already presents the question and choices to the user.

            Args:
                question: The question to ask.
                choices: A list of choice dictionaries, each with a 'label' (display text)
                         and a 'value' (internal value). Example:
                         [{'label': 'Yes', 'value': '0'}, {'label': 'No', 'value': '1'}]

            Returns:
                A MultipleChoiceWidget object representing the question and the choices.

            Raises:
                ValueError: If a choice dictionary is missing 'label' or 'value'.
            """
            parsed_choices = []
            for choice_dict in choices:
                if "label" not in choice_dict or "value" not in choice_dict:
                    raise ValueError(
                        "Each choice dictionary must contain 'label' and 'value' keys."
                    )
                parsed_choices.append(
                    Choice(label=choice_dict["label"], value=choice_dict["value"])
                )

            return MultipleChoiceWidget(
                question=question,
                choices=parsed_choices,
                selected_choice=None,
            )

        def tool_load_excel_data(glob_pattern: str = "*.xlsx") -> str:
            """
            Loads RET (Respiratory Exercise Training) data from Excel files in the RET_DATA_DIR directory.

            Args:
                glob_pattern (str, optional): Pattern to match Excel files. Must end with *.xlsx.
                    Defaults to "*.xlsx" to match all Excel files.

            Returns:
                str: A JSON string containing an array of dictionaries, where each dictionary
                    represents a row from the Excel files. If no files are found, returns an empty array.

            Note:
                The function searches for Excel files in the ./ret_data directory.
                All matching files will be processed and their data combined into a single JSON string.
            """

            data = []

            path = os.path.join(os.path.dirname(__file__), "./ret_data")

            self.logger.info(
                f"Loading RET data from {os.path.join(path, glob_pattern)}"
            )

            for file in glob(os.path.join(path, glob_pattern)):
                df = pd.read_excel(file)
                data.append(df.to_dict(orient="records"))

            return json.dumps(data, default=str)

        def tool_create_bar_chart(
            title: str,
            data: list[dict[str, Any]],
            x_key: str,
            y_keys: list[str],
            horizontal_lines: list[dict[str, Any]] | None = None,
            description: str | None = None,
            y_axis_domain_min: float | None = None,
            y_axis_domain_max: float | None = None,
            height: int = 400,
        ) -> ChartWidget:
            """Create a bar chart.

            Notes for the model:
            • If you provide ``custom_color_role_map`` it **must** be a JSON object, not a
              JSON-encoded string

            ## Data Structure Requirements

            The `data` parameter expects a list of dictionaries where:
            - Each dictionary represents one category (x-axis position)
            - The `x_key` field contains the category name/label and MUST be a string
            - Each `y_key` field contains either:
              1. **Simple value**: A direct number (e.g., `"sales": 1500`)
              2. **Structured value**: `{"value": <number>, "colorRole": "<role_name>"}`

            ### Simple Data Example:
            data = [{"month": "Jan", "sales": 1000, "returns": 50}, {"month": "Feb", "sales": 1200, "returns": 75}]


            ### Advanced Data with Color Roles:
            data = [
                {
                    "month": "Jan",
                    "sales": {"value": 1000, "colorRole": "success"},
                    "returns": {"value": 50, "colorRole": "warning"},
                },
                {
                    "month": "Feb",
                    "sales": {"value": 1200, "colorRole": "success"},
                    "returns": {"value": 75, "colorRole": "neutral"},
                },
            ]


            ## Color System

            ### Built-in Color Roles (use when custom_color_role_map=None):
            - `"success"`: Light green - for positive metrics, achievements
            - `"warning"`: Light orange/red - for alerts, issues requiring attention
            - `"neutral"`: Light blue - for standard/baseline metrics
            - `"info"`: Light yellow - for informational data
            - `"primary"`: Light purple - for primary focus areas
            - `"accent"`: Light cyan - for special highlights
            - `"muted"`: Light gray - for less important data

            ## Horizontal Lines

            The `horizontal_lines` parameter accepts a list of dictionaries, each defining a reference line:
            ```python
            horizontal_lines = [
                {"value": 100, "label": "Target", "color": "#e8f5e8"},
                {"value": 80, "label": "Minimum", "color": "#ffe4e1"},
                {"value": 50},  # Just value, will use default label and color
            ]
            ```

            Required fields:
            - `value` (float): The y-axis value where the line is drawn

            Optional fields:
            - `label` (str): Text label for the line (defaults to None)
            - `color` (str): HEX color code (defaults to black)

            ## Complete Usage Examples

            ### Basic Sales Chart:
            chart = tool_create_bar_chart(
                title="Monthly Sales Performance",
                data=[
                    {"month": "Jan", "sales": 15000, "target": 12000},
                    {"month": "Feb", "sales": 18000, "target": 15000},
                    {"month": "Mar", "sales": 14000, "target": 16000},
                ],
                horizontal_lines=[
                    {"value": 15000, "label": "Target", "color": "#e8f5e8"},
                    {"value": 10000, "label": "Minimum", "color": "#ffe4e1"},
                ],
                x_key="month",
                y_keys=["sales", "target"],
                description="Q1 2024 sales vs targets",
            )

            ### Advanced Chart with Color Coding:
            chart = tool_create_bar_chart(
                title="Department Performance Dashboard",
                data=[
                    {
                        "department": "Sales",
                        "performance": {"value": 95, "colorRole": "success"},
                        "budget_usage": {"value": 80, "colorRole": "neutral"},
                    },
                    {
                        "department": "Marketing",
                        "performance": {"value": 75, "colorRole": "warning"},
                        "budget_usage": {"value": 120, "colorRole": "warning"},
                    },
                ],
                x_key="department",
                y_keys=["performance", "budget_usage"],
                horizontal_lines=[
                    {"value": 100, "label": "Target", "color": "#e8f5e8"},
                    {"value": 50, "label": "Minimum", "color": "#ffe4e1"},
                ],
                y_axis_domain_min=0,
                y_axis_domain_max=150,
                height=500,
            )

            Args:
                title (str): The main title displayed above the chart.

                data (list[dict[str, Any]]): List of data objects. Each object represents one
                    x-axis category. See examples above for structure.

                x_key (str): The dictionary key that contains the x-axis category labels
                    (e.g., "month", "department", "product").

                y_keys (list[str]): List of dictionary keys for the data series to plot as bars.
                    Each key becomes a separate bar series (e.g., ["sales", "returns"]).
                horizontal_lines (list[dict[str, Any]] | None): Optional reference lines drawn across
                    the chart. Each dictionary should contain:
                    - "value" (float, required): The y-axis value where the line is drawn
                    - "label" (str, optional): Text label for the line
                    - "color" (str, optional): HEX color code (e.g., "#000000")

                description (str | None): Optional subtitle/description shown below the title.

                y_axis_domain_min (float | None): Optional minimum value for y-axis scale.
                    Forces chart to start at this value instead of auto-scaling.

                y_axis_domain_max (float | None): Optional maximum value for y-axis scale.
                    Forces chart to end at this value instead of auto-scaling.

                height (int): Chart height in pixels. Defaults to 400.
                    Recommended range: 300-800 pixels.

            Returns:
                ChartWidget: A configured chart widget ready for display in the UI.
                The widget includes all styling, data, and interactive features.

            Raises:
                ValueError: If required keys are missing from data objects, or if color roles
                    are invalid when using built-in color system, or if horizontal_lines
                    have invalid structure.

            Common mistakes:
                - x_key is not a string
                - y_keys are not strings
            """
            # ------------------------------------------------------------------
            # Validate / coerce custom_color_role_map
            # ------------------------------------------------------------------

            # Parse horizontal_lines from dictionaries to Line objects
            parsed_horizontal_lines: list[Line] | None = None
            if horizontal_lines is not None:
                import ast
                import json

                # Step 1 – normalise input to a list of dictionaries
                normalised_lines: list[dict[str, Any]] = []

                # Helper to convert a single string to dict or list
                def _parse_str_to_obj(raw: str) -> list[dict[str, Any]]:
                    raw_s = raw.strip()
                    try:
                        obj = json.loads(raw_s)
                    except json.JSONDecodeError:
                        obj = ast.literal_eval(raw_s)

                    if isinstance(obj, list):
                        return obj  # Expect list[dict]
                    if isinstance(obj, dict):
                        return [obj]
                    raise ValueError(
                        "horizontal_lines string must decode to a dict or list of dicts"
                    )

                if isinstance(horizontal_lines, str):
                    normalised_lines.extend(_parse_str_to_obj(horizontal_lines))
                elif isinstance(horizontal_lines, list):
                    for idx, item in enumerate(horizontal_lines):
                        if isinstance(item, dict):
                            normalised_lines.append(item)
                        elif isinstance(item, str):
                            normalised_lines.extend(_parse_str_to_obj(item))
                        else:
                            raise ValueError(
                                f"horizontal_lines[{idx}] must be a dict or string, got {type(item)}"
                            )
                else:
                    raise ValueError("horizontal_lines must be a list, string, or None")

                # Step 2 – validate dictionaries and convert to Line objects
                parsed_horizontal_lines = []
                for i, line_dict in enumerate(normalised_lines):
                    if not isinstance(line_dict, dict):
                        raise ValueError(
                            f"horizontal_lines[{i}] must be a dictionary after parsing, got {type(line_dict)}"
                        )

                    if "value" not in line_dict:
                        raise ValueError(
                            f"horizontal_lines[{i}] missing required 'value' field"
                        )

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

                    parsed_horizontal_lines.append(
                        Line(value=value, label=label, color=color)
                    )

            return ChartWidget.create_bar_chart(
                title=title,
                data=data,
                x_key=x_key,
                y_keys=y_keys,
                description=description,
                height=height,
                horizontal_lines=parsed_horizontal_lines,
                y_axis_domain_min=y_axis_domain_min,
                y_axis_domain_max=y_axis_domain_max,
            )

        def tool_create_line_chart(
            title: str,
            data: list[dict[str, Any]],
            x_key: str,
            y_keys: list[str],
            y_labels: list[str] | None = None,
            custom_series_colors_palette: list[str] | None = None,
            horizontal_lines: list[Line] | None = None,
            description: str | None = None,
            height: int = 400,
            y_axis_domain_min: float | None = None,
            y_axis_domain_max: float | None = None,
        ) -> ChartWidget:
            """
            Creates a line chart with customizable line colors and optional horizontal lines.
            Each line series will have a distinct color.

            Data Structure for `data` argument:
            Each item in the `data` list is a dictionary representing a point on the x-axis.
            For each `y_key` you want to plot, its value in the dictionary MUST be the
            direct numerical value for that data point (or null for missing data).

            Line Colors:
            The color of the lines themselves is determined by `custom_series_colors_palette`.
            If `custom_series_colors_palette` is not provided, a default palette is used.
            The Nth line (corresponding to the Nth key in `y_keys`) will use the Nth color from this palette.

            Args:
                title (str): Chart title.
                data (list[dict[str, Any]]): List of data objects as described above.
                    Example:
                    [
                        {{"date": "2024-01-01", "temp": 10, "humidity": 60}},
                        {{"date": "2024-01-02", "temp": 12, "humidity": 65}},
                        {{"date": "2024-01-03", "temp": 9, "humidity": null}} // null for missing humidity
                    ]
                **Important** Do not add colors in the data object for line charts.
                x_key (str): Key in data objects for the x-axis (e.g., 'date').
                y_keys (list[str]): Keys for y-axis values (e.g., ['temp', 'humidity']).
                y_labels (list[str] | None): Optional labels for y-axis series. If None,
                                            `y_keys` are used. Must match `y_keys` length.
                custom_series_colors_palette (list[str] | None): Optional. A list of HEX color strings
                                     to define the colors for each **line series**.
                                     Example: ["#007bff", "#28a745"] for two lines.
                horizontal_lines (list[Line] | None): Optional. List of `Line` objects for horizontal lines.
                                     See `tool_create_bar_chart` for `Line` model details.
                                     Example: `[Line(value=10, label="Threshold")]`
                description (str | None): Optional chart description.
                height (int): Chart height in pixels. Defaults to 400.
                y_axis_domain_min (float | None): Optional. Sets the minimum value for the Y-axis scale.
                y_axis_domain_max (float | None): Optional. Sets the maximum value for the Y-axis scale.
            Returns:
                A ChartWidget object configured as a line chart.
            """
            if y_labels is not None and len(y_keys) != len(y_labels):
                raise ValueError(
                    "If y_labels are provided for line chart, they must match the length of y_keys."
                )

            # Basic validation for data structure (can be enhanced)
            for item in data:
                if x_key not in item:
                    raise ValueError(
                        f"Line chart data item missing x_key '{x_key}': {item}"
                    )
                for y_key in y_keys:
                    if y_key in item and not isinstance(
                        item[y_key], (int, float, type(None))
                    ):
                        if isinstance(
                            item[y_key], str
                        ):  # Allow string if it's meant to be a number
                            try:
                                float(item[y_key])
                            except ValueError:
                                raise ValueError(
                                    f"Line chart data for y_key '{y_key}' has non-numeric value '{item[y_key]}'. Must be number or null."
                                )
                        else:
                            raise ValueError(
                                f"Line chart data for y_key '{y_key}' has non-numeric value '{item[y_key]}'. Must be number or null."
                            )

            return ChartWidget.create_line_chart(
                title=title,
                data=data,
                x_key=x_key,
                y_keys=y_keys,
                y_labels=y_labels,
                description=description,
                height=height,
                horizontal_lines=horizontal_lines,
                custom_series_colors_palette=custom_series_colors_palette,
                y_axis_domain_min=y_axis_domain_min,
                y_axis_domain_max=y_axis_domain_max,
            )

        return [
            tool_search_documents,
            tool_get_document_contents,
            tool_ask_multiple_choice,
            tool_load_excel_data,
            tool_create_bar_chart,
            tool_create_line_chart,
            *easylog_sql_tools.all_tools,
            *easylog_backend_tools.all_tools,
            BaseTools.tool_noop,
        ]

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam], _: int = 0
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        tools = self.get_tools()

        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {
                    "role": "developer",
                    "content": self.config.prompt,
                },
                *messages,
            ],
            stream=True,
            tools=[function_to_openai_tool(tool) for tool in tools],
            tool_choice="auto",
        )

        return response, tools
