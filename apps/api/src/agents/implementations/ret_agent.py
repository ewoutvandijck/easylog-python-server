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

            return "\n-".join([f"Path: {document.path} - Summary: {document.summary}" for document in result])

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

        def tool_ask_multiple_choice(question: str, choices: list[dict[str, str]]) -> MultipleChoiceWidget:
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
                    raise ValueError("Each choice dictionary must contain 'label' and 'value' keys.")
                parsed_choices.append(Choice(label=choice_dict["label"], value=choice_dict["value"]))

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

            self.logger.info(f"Loading RET data from {os.path.join(path, glob_pattern)}")

            for file in glob(os.path.join(path, glob_pattern)):
                df = pd.read_excel(file)
                data.append(df.to_dict(orient="records"))

            return json.dumps(data, default=str)

        def tool_create_bar_chart(
            title: str,
            data: list[dict[str, Any]],
            x_key: str,
            y_keys: list[str],
            y_labels: list[str] | None = None,
            custom_color_role_map: dict[str, str] | None = None,
            custom_series_colors_palette: list[str] | None = None,
            horizontal_lines: list[Line] | None = None,
            description: str | None = None,
            y_axis_domain_min: float | None = None,
            y_axis_domain_max: float | None = None,
            height: int = 400,
        ) -> ChartWidget:
            """
            Creates a bar chart with customizable colors and optional horizontal lines.

            You MUST provide data where each y_key's value is a dictionary:
            {{"value": <actual_value>, "colorRole": <role_name_str> | null}}.
            - If `colorRole` is a string (e.g., "high_sales", "low_stock"), it will be
              used as a key to look up the color. The lookup order is:
              1. `custom_color_role_map` (if provided)
              2. The default chart color roles (e.g., "success", "warning", "neutral", "info", "primary", etc. Current default map: {DEFAULT_COLOR_ROLE_MAP.keys()})
              If the role is not found in any map, a default series color is used for the bar.
            - If `colorRole` is null, the chart widget will assign a default color for that
              bar based on its series.

            Args:
                title (str): Chart title.
                data (list[dict[str, Any]]): List of data objects.
                    Example:
                    [
                        {{"month": "Jan", "sales": {{"value": 100, "colorRole": "neutral"}}, "returns": {{"value": 10, "colorRole": "warning"}}}},
                        {{"month": "Feb", "sales": {{"value": 150, "colorRole": "success"}}, "returns": {{"value": 12, "colorRole": null}}}}
                    ]
                x_key (str): Key in data objects for the x-axis (e.g., 'month').
                y_keys (list[str]): Keys for y-axis values (e.g., ['sales', 'returns']).
                y_labels (list[str] | None): Optional labels for y-axis values. If None,
                                            `y_keys` are used. Must match `y_keys` length.
                custom_color_role_map (dict[str, str] | None): Optional. A dictionary to
                                     define custom mappings from `colorRole` strings (provided in `data`)
                                     to specific HEX color codes (e.g., '#RRGGBB').
                                     Example: {{"high_sales": "#4CAF50", "low_sales": "#F44336"}}
                custom_series_colors_palette (list[str] | None): Optional. A list of HEX color strings
                                     to define the default colors for each series (y_key).
                                     If not provided, a default palette is used.
                                     Example: ["#FF0000", "#00FF00"] for two series.
                horizontal_lines (list[Line] | None): Optional. A list of `Line` objects to
                                     draw horizontal lines across the chart. Each `Line` object
                                     defines the y-axis value, an optional label, and an optional color.
                                     The `Line` model requires:
                                     - `value` (float): The y-axis value where the line is drawn.
                                     - `label` (str | None): Optional text label for the line.
                                     - `color` (str | None): Optional HEX color (e.g., '#000000' for black).
                                       Defaults to black if not specified.
                                     Example:
                                     `[Line(value=80, label="Target Sales", color="#FF0000"), Line(value=50)]`
                description (str | None): Optional chart description.
                height (int): Chart height in pixels. Defaults to 400.
                y_axis_domain_min (float | None): Optional. Sets the minimum value for the Y-axis scale.
                y_axis_domain_max (float | None): Optional. Sets the maximum value for the Y-axis scale.
            Returns:
                A ChartWidget object.
            """

            return ChartWidget.create_bar_chart(
                title=title,
                data=data,
                x_key=x_key,
                y_keys=y_keys,
                y_labels=y_labels,
                description=description,
                height=height,
                horizontal_lines=horizontal_lines,
                custom_color_role_map=custom_color_role_map,
                custom_series_colors_palette=custom_series_colors_palette,
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
                raise ValueError("If y_labels are provided for line chart, they must match the length of y_keys.")

            # Basic validation for data structure (can be enhanced)
            for item in data:
                if x_key not in item:
                    raise ValueError(f"Line chart data item missing x_key '{x_key}': {item}")
                for y_key in y_keys:
                    if y_key in item and not isinstance(item[y_key], (int, float, type(None))):
                        if isinstance(item[y_key], str):  # Allow string if it's meant to be a number
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
