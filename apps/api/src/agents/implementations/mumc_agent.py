import io
import json
import re
import uuid
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any, Literal

import httpx
import pytz
from onesignal.model.notification import Notification
from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from PIL import Image, ImageOps
from prisma.enums import health_data_point_type
from prisma.types import health_data_pointsWhereInput, usersWhereInput
from pydantic import BaseModel, Field
from src.agents.base_agent import BaseAgent, SuperAgentConfig
from src.agents.tools.base_tools import BaseTools
from src.agents.tools.easylog_backend_tools import EasylogBackendTools
from src.agents.tools.easylog_sql_tools import EasylogSqlTools
from src.lib.prisma import prisma
from src.models.chart_widget import (
    DEFAULT_COLOR_ROLE_MAP,
    ChartWidget,
    Line,
    TooltipConfig,
    ZLMDataRow,
)
from src.models.multiple_choice_widget import Choice, MultipleChoiceWidget
from src.settings import settings
from src.utils.function_to_openai_tool import function_to_openai_tool


class QuestionaireQuestionConfig(BaseModel):
    question: str = Field(
        default="",
        description="The text of the question to present to the user. This should be a clear, direct question that elicits the desired information.",
    )
    instructions: str = Field(
        default="",
        description="Additional guidance or context for the ai agent on how to answer the question, such as language requirements or format expectations.",
    )
    name: str = Field(
        default="",
        description="A unique identifier for this question, used for referencing the answer in prompts or logic. For example, if the question is 'What is your name?', the name could be 'user_name', allowing you to use {questionaire.user_name.answer} in templates.",
    )


class RoleConfig(BaseModel):
    name: str = Field(
        default="EasyLogAssistant",
        description="The display name of the role, used to identify and select this role in the system.",
    )
    prompt: str = Field(
        default="Je bent een vriendelijke assistent die helpt met het geven van demos van wat je allemaal kan",
        description="The system prompt or persona instructions for this role, defining its behavior and tone.",
    )
    model: str = Field(
        default="anthropic/claude-sonnet-4",
        description="The model identifier to use for this role, e.g., 'anthropic/claude-sonnet-4' or any model from https://openrouter.ai/models.",
    )
    tools_regex: str = Field(
        default=".*",
        description="A regular expression specifying which tools this role is permitted to use. Use '.*' to allow all tools, or restrict as needed.",
    )
    allowed_subjects: list[str] | None = Field(
        default=None,
        description="A list of subject names from the knowledge base that this role is allowed to access. If None, all subjects are allowed.",
    )
    questionaire: list[QuestionaireQuestionConfig] = Field(
        default_factory=list,
        description="A list of questions (as QuestionaireQuestionConfig) that this role should ask the user, enabling dynamic, role-specific data collection.",
    )


class MUMCAgentConfig(BaseModel):
    roles: list[RoleConfig] = Field(
        default_factory=lambda: [
            RoleConfig(
                name="MUMCAssistant",
                prompt="Je bent een vriendelijke assistent die helpt met het geven van demos van wat je allemaal kan",
                model=r"anthropic\/claude-sonnet-4",
                tools_regex=".*",
                allowed_subjects=None,
                questionaire=[],
            )
        ]
    )
    prompt: str = Field(
        default="You can use the following roles: {available_roles}.\nYou are currently acting as the role: {current_role}.\nYour specific instructions for this role are: {current_role_prompt}.\nThis prompt may include details from a questionnaire. Use the provided tools to interact with the questionnaire if needed.\nThe current time is: {current_time}.\nRecurring tasks: {recurring_tasks}\nReminders: {reminders}\nMemories: {memories}"
    )


class MUMCAgent(BaseAgent[MUMCAgentConfig]):
    async def get_current_role(self) -> RoleConfig:
        role = await self.get_metadata("current_role", self.config.roles[0].name)
        if role not in [role.name for role in self.config.roles]:
            role = self.config.roles[0].name

        return next(
            role_config for role_config in self.config.roles if role_config.name == role
        )

    def get_tools(self) -> dict[str, Callable]:
        # EasyLog-specific tools
        easylog_token = self.request_headers.get("x-easylog-bearer-token", "")
        easylog_backend_tools = EasylogBackendTools(
            bearer_token=easylog_token,
            base_url=settings.EASYLOG_API_URL,
        )

        if easylog_token:
            pass  # Token available for EasyLog tools

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

        # Role management tool
        async def tool_set_current_role(role: str) -> str:
            """Set the current role for the agent.

            Args:
                role (str): The role to set.

            Raises:
                ValueError: If the role is not found in the roles.
            """

            if role not in [role.name for role in self.config.roles]:
                raise ValueError(f"Role {role} not found in roles")

            await self.set_metadata("current_role", role)

            return f"Gewijzigd naar rol {role}"

        # Document search tools
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
                     - The document's path and summary
            """

            result = await self.search_documents(
                search_query, subjects=(await self.get_current_role()).allowed_subjects
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

        # Questionnaire tools
        async def tool_answer_questionaire_question(
            question_name: str, answer: str
        ) -> str:
            """Answer a question from the questionaire.

            Args:
                question_name (str): The name of the question to answer.
                answer (str): The answer to the question.
            """

            await self.set_metadata(question_name, answer)

            return f"Answer to {question_name} set to {answer}"

        async def tool_get_questionaire_answer(question_name: str) -> str:
            """Get the answer to a question from the questionaire.

            Args:
                question_name (str): The name of the question to get the answer to.

            Returns:
                str: The answer to the question.
            """
            return await self.get_metadata(question_name, "[not answered]")

        # Visualization tools
        def tool_create_zlm_chart(
            language: Literal["nl", "en"],
            data: list[dict[str, Any]],
            x_key: str,
            y_keys: list[str],
            y_labels: list[str] | None = None,
            height: int = 1000,
        ) -> ChartWidget:
            """
            Creates a ZLM (Ziektelastmeter COPD) bar chart using a predefined ZLM color scheme.
            The chart visualizes scores as percentages, expecting values in the **0-100 range**.

            Args:
                language: The language for chart title and description ('nl' or 'en').
                data: The data for the chart. Each dictionary in the list represents a
                      point or group on the x-axis.
                      - Each dictionary MUST contain the `x_key` field.
                      - For each `y_key` specified in `y_keys`, the dictionary MUST
                        contain a field with that `y_key` name.
                      - The value associated with each `y_key` MUST be a dictionary
                        with two keys:
                        1.  `"value"`: A numerical percentage (float or integer).
                            **IMPORTANT: This value MUST be between 0 and 100 (inclusive).**
                            For example, 75 represents 75%. Do NOT use values like 0.75.
                        2.  `"colorRole"`: A string that MUST be one of "success",
                            "warning", or "neutral". This role will be mapped to specific
                            ZLM colors. 0-40 = warning, 40-70 = neutral, 70-100 = success.
                      - Example (single y-key):
                        `data=[{"category": "Lung Function", "score": {"value": 65, "colorRole": "neutral"}},`
                              `{"category": "Symptoms", "score": {"value": 30, "colorRole": "warning"}}]`
                        (if x_key="category", y_keys=["score"])
                      - Example (multiple y-keys):
                        `data=[{"month": "Jan", "metric_a": {"value": 85, "colorRole": "success"}, "metric_b": {"value": 45, "colorRole": "warning"}},`
                              `{"month": "Feb", "metric_a": {"value": 90, "colorRole": "success"}, "metric_b": {"value": 50, "colorRole": "neutral"}}]`
                        (if x_key="month", y_keys=["metric_a", "metric_b"])
                x_key: The key in each data dictionary that represents the x-axis value
                       (e.g., "category", "month").
                y_keys: A list of keys in each data dictionary that represent the y-axis
                        values. (e.g., `["score"]`, `["metric_a", "metric_b"]`)
                y_labels: Optional. Custom labels for each y-series. If None, `y_keys`
                          will be used as labels. **IMPORTANT**: Must have the same length as `y_keys`
                          if provided.
                height: Optional. The height of the chart in pixels. Defaults to 400.

            Returns:
                A ChartWidget object configured for ZLM display!

            Raises:
                ValueError: If data is missing required keys, values are not numbers,
                            percentages are outside the 0-100 range, or colorRole is invalid.
            """

            title = (
                "Resultaten ziektelastmeter COPD %"
                if language == "nl"
                else "Disease burden results %"
            )
            description = (
                "Uw ziektelastmeter COPD resultaten."
                if language == "nl"
                else "Your COPD burden results."
            )

            # Custom color role map for ZLM charts
            ZLM_CUSTOM_COLOR_ROLE_MAP: dict[str, str] = {
                # We only use a custom neutral color, the rest is re-used.
                "success": DEFAULT_COLOR_ROLE_MAP["success"],
                "neutral": "#ffdaaf",  # Pastel orange
                "warning": DEFAULT_COLOR_ROLE_MAP["warning"],
            }

            horizontal_lines = None

            # Data validation for ZLM charts
            for raw_item_idx, raw_item in enumerate(data):
                if x_key not in raw_item:
                    raise ValueError(
                        f"Missing x_key '{x_key}' in ZLM data item at index {raw_item_idx}: {raw_item}"
                    )
                current_x_value = raw_item[x_key]

                for y_key in y_keys:
                    if y_key not in raw_item:
                        # Skip missing keys - handled by chart widget
                        continue

                    value_container = raw_item[y_key]
                    if not (
                        isinstance(value_container, dict)
                        and "value" in value_container
                        and "colorRole" in value_container  # LLM must provide colorRole
                    ):
                        raise ValueError(
                            f"Data for y_key '{y_key}' in x_value '{current_x_value}' (index {raw_item_idx}) "
                            "for ZLM chart is not in the expected format: "
                            "{'value': <percentage_0_to_100>, 'colorRole': <'success'|'warning'|'neutral'|null>}. "
                            f"Received: {value_container}"
                        )

                    val_from_container = value_container["value"]
                    if not isinstance(val_from_container, (int, float)):
                        raise ValueError(
                            f"ZLM chart 'value' for y_key '{y_key}' (x_value '{current_x_value}', index {raw_item_idx}) "
                            f"must be a number, got: {val_from_container} (type: {type(val_from_container).__name__})"
                        )

                    val_float = float(val_from_container)
                    if not (0.0 <= val_float <= 100.0):
                        # Check for common 0-1 scale mistake
                        hint = ""
                        if 0 < val_from_container <= 1.0:
                            hint = f" (Value {val_from_container} looks like 0-1 scale; use 0-100 range)"
                        raise ValueError(
                            f"ZLM chart value {val_from_container} for '{y_key}' is outside 0-100 range{hint}"
                        )

                    role_from_data = value_container["colorRole"]
                    if (
                        role_from_data is not None
                        and role_from_data not in ZLM_CUSTOM_COLOR_ROLE_MAP
                    ):
                        raise ValueError(
                            f"Invalid colorRole '{role_from_data}' for '{y_key}'. "
                            f"Must be one of {list(ZLM_CUSTOM_COLOR_ROLE_MAP.keys())} or null"
                        )

            chart = ChartWidget.create_bar_chart(
                title=title,
                description=description,
                data=data,
                x_key=x_key,
                y_keys=y_keys,
                height=height,
                custom_color_role_map=ZLM_CUSTOM_COLOR_ROLE_MAP,
                horizontal_lines=horizontal_lines,
                y_axis_domain_min=0,
                y_axis_domain_max=100,
            )

            # Configure tooltip to hide domain labels and show only percentage

            chart.tooltip = TooltipConfig(show=True, hide_label=True)

            return chart

        def tool_create_zlm_balloon_chart(
            language: Literal["nl", "en"],
            data: list[ZLMDataRow] | list[dict[str, Any]] | str,
        ) -> ChartWidget:
            """
            Creates a ZLM (Ziektelastmeter COPD) balloon chart using the official ZLM scoring system.
            Uses complex domain-specific scoring logic with original ZLM cutoff points and rules.
            Scores are expected in the **0-6 range** as per ZLM COPD guidelines.

            Args:
                language: The language for chart title and description ('nl' or 'en').
                data: A list of `ZLMDataRow` objects, dictionaries, or a JSON string representing the chart data.
                      Each item represents a category on the x-axis and its corresponding scores.
                      - If using dictionaries, each should contain:
                        - `x_value` (str): The name of the category (e.g., "Longklachten").
                        - `y_current` (float): The current score (0-6).
                        - `y_old` (float | None): Optional. The previous score the patient had (0-6).
                        - `y_label` (str): The label for the y-axis, typically "Score (0-6)".

            Returns:
                A ChartWidget object configured as a balloon chart with domain-specific ZLM scoring.

            Note:
                Uses original ZLM COPD scoring logic with specific cutoff points per domain:
                - Longklachten: Complex logic based on average + individual kortademig in rust check
                - Longaanvallen: Discrete values (0=100%, 1=50%, 2+=0%)
                - Other domains: Specific cutoff points as per ZLM documentation

            Example:
                ```python
                data = [
                    {"x_value": "Longklachten", "y_current": 2.5, "y_old": 3.0, "y_label": "Score (0-6)"},
                    {"x_value": "Vermoeidheid", "y_current": 1.2, "y_old": 1.8, "y_label": "Score (0-6)"},
                ]
                chart_widget = tool_create_zlm_balloon_chart(language="nl", data=data)
                ```
            """
            title = "Dit zijn uw resultaten"
            description = None

            # Validate input data
            if not data or len(data) == 0:
                raise ValueError("Data list must contain at least one item.")

            # Handle JSON string input by parsing it first and ensure proper typing
            processed_data: list[ZLMDataRow] | list[dict[str, Any]]
            if isinstance(data, str):
                try:
                    import json

                    parsed_data = json.loads(data)
                    if not isinstance(parsed_data, list):
                        raise ValueError("JSON string must represent a list")
                    processed_data = parsed_data
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON string provided: {e}")
            else:
                processed_data = data

            # Apply domain-specific ZLM COPD scoring logic
            converted_data = []

            for i, item in enumerate(processed_data):
                if isinstance(item, dict):
                    # Validate required keys
                    required_keys = ["x_value", "y_current", "y_label"]
                    for key in required_keys:
                        if key not in item:
                            raise ValueError(
                                f"Missing required key '{key}' in data item {i}: {item}"
                            )

                    # Validate score ranges
                    current_score = item["y_current"]
                    old_score = item.get("y_old")
                    domain_name = str(item["x_value"])

                    if not isinstance(current_score, (int, float)):
                        raise ValueError(f"Current score must be numeric for item {i}")

                    if not (0 <= current_score <= 6):
                        raise ValueError(
                            f"ZLM score {current_score} outside range 0-6 for item {i}"
                        )

                    if old_score is not None:
                        if not isinstance(old_score, (int, float)):
                            raise ValueError(f"Old score must be numeric for item {i}")
                        if not (0 <= old_score <= 6):
                            raise ValueError(
                                f"ZLM old score {old_score} outside range 0-6 for item {i}"
                            )

                    # Apply domain-specific scoring logic
                    current_height = self._calculate_zlm_balloon_height(
                        domain_name, current_score, processed_data
                    )
                    old_height = (
                        self._calculate_zlm_balloon_height(
                            domain_name, old_score, processed_data
                        )
                        if old_score is not None
                        else None
                    )

                    # Convert balloon height percentages (0-100%) to Flutter Y-values (0-10 scale)
                    flutter_y_current = current_height / 10.0
                    flutter_y_old = (
                        old_height / 10.0 if old_height is not None else None
                    )

                    converted_data.append(
                        ZLMDataRow(
                            x_value=domain_name,
                            y_current=flutter_y_current,
                            y_old=flutter_y_old,
                            y_label="Score (0-6)",
                            tooltip_score=current_score,  # Store original 0-6 score for tooltip
                            tooltip_old_score=old_score,  # Store original 0-6 old score for tooltip
                        )
                    )

                elif hasattr(item, "y_current"):
                    # ZLMDataRow object validation
                    if not (0 <= item.y_current <= 6):
                        raise ValueError(
                            f"ZLM score {item.y_current} outside range 0-6 for item {i}"
                        )

                    if item.y_old is not None and not (0 <= item.y_old <= 6):
                        raise ValueError(
                            f"ZLM old score {item.y_old} outside range 0-6 for item {i}"
                        )

                    # Apply domain-specific scoring logic
                    current_height = self._calculate_zlm_balloon_height(
                        item.x_value, item.y_current, processed_data
                    )
                    old_height = (
                        self._calculate_zlm_balloon_height(
                            item.x_value, item.y_old, processed_data
                        )
                        if item.y_old is not None
                        else None
                    )

                    # Convert balloon height percentages (0-100%) to Flutter Y-values (0-10 scale)
                    flutter_y_current = current_height / 10.0
                    flutter_y_old = (
                        old_height / 10.0 if old_height is not None else None
                    )

                    converted_data.append(
                        ZLMDataRow(
                            x_value=item.x_value,
                            y_current=flutter_y_current,
                            y_old=flutter_y_old,
                            y_label="Score (0-6)",
                            tooltip_score=item.y_current,  # Store original 0-6 score for tooltip
                            tooltip_old_score=item.y_old,  # Store original 0-6 old score for tooltip
                        )
                    )
                else:
                    raise ValueError(
                        f"Invalid data item at index {i}: expected dict or ZLMDataRow"
                    )

            return ChartWidget.create_balloon_chart(
                title=title,
                description=description,
                data=converted_data,
            )

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
                    raise ValueError("horizontal_lines string must decode to a dict or list of dicts")

                if isinstance(horizontal_lines, str):
                    normalised_lines.extend(_parse_str_to_obj(horizontal_lines))
                elif isinstance(horizontal_lines, list):
                    for idx, item in enumerate(horizontal_lines):
                        if isinstance(item, dict):
                            normalised_lines.append(item)
                        elif isinstance(item, str):
                            normalised_lines.extend(_parse_str_to_obj(item))
                        else:
                            raise ValueError(f"horizontal_lines[{idx}] must be a dict or string, got {type(item)}")
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
                        raise ValueError(f"horizontal_lines[{i}] 'color' must be a string, got {type(color)}")

                    parsed_horizontal_lines.append(Line(value=value, label=label, color=color))

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
            height: int = 600,
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

        # Interaction tools
        def tool_ask_multiple_choice(
            question: str, choices: list[dict[str, str]]
        ) -> tuple[MultipleChoiceWidget, bool]:
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
            ), True

        # Image tools
        def tool_download_image(url: str) -> Image.Image:
            """Download an image from a URL.

            Args:
                url (str): The URL of the image to download.

            Returns:
                Image.Image: The downloaded image.

            Raises:
                httpx.HTTPStatusError: If the download fails.
                PIL.UnidentifiedImageError: If the content is not a valid image.
                Exception: For other potential errors during download or processing.
            """
            try:
                response = httpx.get(url, timeout=10)
                response.raise_for_status()

                image = Image.open(io.BytesIO(response.content))

                ImageOps.exif_transpose(image, in_place=True)

                if image.mode in ("RGBA", "LA", "P"):
                    image = image.convert("RGB")

                max_size = 768
                if image.width > max_size or image.height > max_size:
                    ratio = min(max_size / image.width, max_size / image.height)
                    new_size = (int(image.width * ratio), int(image.height * ratio))
                    self.logger.info(
                        f"Resizing image from {image.width}x{image.height} to {new_size[0]}x{new_size[1]}"
                    )
                    image = image.resize(new_size, Image.Resampling.LANCZOS)

                return image

            except httpx.HTTPStatusError:
                raise
            except Image.UnidentifiedImageError:
                raise
            except Exception:
                raise

        # Schedule and reminder tools
        async def tool_set_recurring_task(cron_expression: str, task: str) -> str:
            """Set a schedule for a task. The tasks will be part of the system prompt, so you can use them to figure out what needs to be done today.

            Args:
                cron_expression (str): The cron expression to set.
                task (str): The task to set the schedule for.
            """

            existing_tasks: list[dict[str, str]] = await self.get_metadata(
                "recurring_tasks", []
            )

            existing_tasks.append(
                {
                    "id": str(uuid.uuid4())[:8],
                    "cron_expression": cron_expression,
                    "task": task,
                }
            )

            await self.set_metadata("recurring_tasks", existing_tasks)

            return f"Schedule set for {task} with cron expression {cron_expression}"

        async def tool_add_reminder(date: str, message: str) -> str:
            """Add a reminder.

            Args:
                date (str): The date and time of the reminder in ISO 8601 format.
                message (str): The message to remind the user about.
            """

            existing_reminders: list[dict[str, str]] = await self.get_metadata(
                "reminders", []
            )

            existing_reminders.append(
                {
                    "id": str(uuid.uuid4())[:8],
                    "date": date,
                    "message": message,
                }
            )

            await self.set_metadata("reminders", existing_reminders)

            return f"Reminder added for {message} at {date}"

        async def tool_remove_recurring_task(id: str) -> str:
            """Remove a recurring task.

            Args:
                id (str): The ID of the task to remove.
            """
            existing_tasks: list[dict[str, str]] = await self.get_metadata(
                "recurring_tasks", []
            )

            existing_tasks = [task for task in existing_tasks if task["id"] != id]

            await self.set_metadata("recurring_tasks", existing_tasks)

            return f"Recurring task {id} removed"

        async def tool_remove_reminder(id: str) -> str:
            """Remove a reminder.

            Args:
                id (str): The ID of the reminder to remove.
            """
            existing_reminders: list[dict[str, str]] = await self.get_metadata(
                "reminders", []
            )

            existing_reminders = [
                reminder for reminder in existing_reminders if reminder["id"] != id
            ]

            await self.set_metadata("reminders", existing_reminders)

            return f"Reminder {id} removed"

        # Memory tools
        async def tool_store_memory(memory: str) -> str:
            """Store a memory.

            Args:
                memory (str): The memory to store.
            """

            memories = await self.get_metadata("memories", [])
            memories.append({"id": str(uuid.uuid4())[0:8], "memory": memory})
            await self.set_metadata("memories", memories)

            return f"Memory stored: {memory}"

        async def tool_get_memory(id: str) -> str:
            """Get a memory.

            Args:
                id (str): The id of the memory to get.
            """
            memories = await self.get_metadata("memories", [])
            memory = next((m for m in memories if m["id"] == id), None)
            if memory is None:
                return "[not stored]"

            return memory["memory"]

        async def tool_send_notification(title: str, contents: str) -> str:
            """Send a notification.

            Args:
                title (str): The title of the notification.
                contents (str): The text to send in the notification.
            """
            onesignal_id = self.request_headers.get(
                "x-onesignal-external-user-id"
            ) or await self.get_metadata("onesignal_id", None)

            assistant_field_name = self.request_headers.get(
                "x-assistant-field-name"
            ) or await self.get_metadata("assistant_field_name", None)

            self.logger.info(f"Sending notification to {onesignal_id}")

            if onesignal_id is None:
                return "No onesignal id found"

            if assistant_field_name is None:
                return "No assistant field name found"

            notification = Notification(
                target_channel="push",
                channel_for_external_user_ids="push",
                app_id=settings.ONESIGNAL_APP_ID,
                include_external_user_ids=[onesignal_id],
                contents={"en": contents},
                headings={"en": title},
                data={"type": "chat", "assistantFieldName": assistant_field_name},
            )

            self.logger.info(f"Notification: {notification}")

            response = await self.one_signal.send_notification(notification)
            self.logger.info(f"Notification response: {response}")

            notifications = await self.get_metadata("notifications", [])
            notifications.append(
                {
                    "id": response["id"],
                    "title": title,
                    "contents": contents,
                    "sent_at": datetime.now().isoformat(),
                }
            )

            await self.set_metadata("notifications", notifications)

            return "Notification sent"

        # Step counter tools
        async def tool_get_date_time() -> str:
            """Get the current date and time in ISO 8601 format YYYY-MM-DD HH:MM:SS."""
            return datetime.now().isoformat()

        async def tool_get_steps_data(
            date_from: str | datetime,
            date_to: str | datetime,
            aggregation: Literal["hour", "day", None] | None = None,
        ) -> list[dict[str, Any]]:
            """Get the steps data for a user with optional aggregation.
            Make sure to use the tool_get_date_time tool to get the actual current date and time.

            Args:
                date_from (str | datetime): The start date/time in ISO 8601 format (YYYY-MM-DD HH:MM:SS) or a datetime object.
                date_to   (str | datetime): The end date/time in ISO 8601 format (YYYY-MM-DD HH:MM:SS) or a datetime object.
                aggregation (Literal["hour", "day", None], optional):
                    - "hour":   Return total steps per **hour** within range.
                    - "day":    Return total steps per **day** within range.
                    - None (default): Return raw, un-aggregated datapoints.

            Returns:
                list[dict[str, Any]]: Depending on aggregation level:
                    - Raw points:   [{"created_at": "...", "value": 123}, ...]
                    - Per hour:     [{"bucket": "YYYY-MM-DD HH:00:00", "value": 456}, ...]
                    - Per day:      [{"bucket": "YYYY-MM-DD", "value": 789}, ...]
            """
            external_user_id = self.request_headers.get("x-onesignal-external-user-id")

            if external_user_id is None:
                raise ValueError("User ID not provided and not found in agent context.")

            user = await prisma.users.find_first(
                where=usersWhereInput(external_id=external_user_id)
            )
            if user is None:
                raise ValueError("User not found")

            print("Retrieving steps data for user", user.id)
            date_from = (
                datetime.fromisoformat(date_from)
                if isinstance(date_from, str)
                else date_from
            )
            date_to = (
                datetime.fromisoformat(date_to) if isinstance(date_to, str) else date_to
            )

            # If both inputs refer to the same calendar date and no explicit time was
            # provided (i.e. they are at midnight), extend `date_to` to the end of that day
            if (
                date_from.date() == date_to.date()
                and date_from.time() == datetime.min.time()
                and date_to.time() == datetime.min.time()
            ):
                date_to = date_to.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )

            steps_data = await prisma.health_data_points.find_many(
                where=health_data_pointsWhereInput(
                    user_id=user.id,
                    type=health_data_point_type.steps,
                    date_from={
                        "gte": date_from,
                    },
                    date_to={
                        "lte": date_to,
                    },
                ),
                order={"created_at": "asc"},
            )

            if not steps_data:
                print("No steps data found for user between", date_from, "and", date_to)
                return []

            if aggregation in {"hour", "day"}:
                trunc_unit = aggregation

                rows: list[dict[str, Any]] = await prisma.query_raw(
                    f"""
                    SELECT
                        date_trunc('{trunc_unit}', date_from) AS bucket,
                        SUM(value)::int                     AS total
                    FROM health_data_points
                    WHERE user_id = $1::uuid
                        AND type     = 'steps'
                        AND date_from >= $2::timestamp
                        AND date_to   <= $3::timestamp
                    GROUP BY bucket
                    ORDER BY bucket
                    """,
                    user.id,
                    date_from,
                    date_to,
                )

                return [
                    {"created_at": row["bucket"], "value": row["total"]} for row in rows
                ]

            return [
                {
                    "created_at": step.created_at.isoformat(),
                    "date_from": step.date_from.isoformat(),
                    "date_to": step.date_to.isoformat(),
                    "value": step.value,
                }
                for step in steps_data
            ]

        # Assemble and return the complete tool list
        tools_list = [
            # EasyLog-specific tools
            *easylog_backend_tools.all_tools,
            *easylog_sql_tools.all_tools,
            # Role management
            tool_set_current_role,
            # Document tools
            tool_search_documents,
            tool_get_document_contents,
            # Questionnaire tools
            tool_answer_questionaire_question,
            tool_get_questionaire_answer,
            # Visualization tools
            tool_create_bar_chart,
            tool_create_zlm_chart,
            tool_create_zlm_balloon_chart,
            tool_create_line_chart,
            # Interaction tools
            tool_ask_multiple_choice,
            # Image tools
            tool_download_image,
            # Schedule and reminder tools
            tool_set_recurring_task,
            tool_add_reminder,
            tool_remove_recurring_task,
            tool_remove_reminder,
            # Memory tools
            tool_store_memory,
            tool_get_memory,
            # Notification tool
            tool_send_notification,
            # Step counter tools
            tool_get_date_time,
            tool_get_steps_data,
            # System tools
            BaseTools.tool_noop,
            BaseTools.tool_call_super_agent,
        ]
        return {tool.__name__: tool for tool in tools_list}

    def _calculate_zlm_balloon_height(
        self,
        domain_name: str,
        score: float,
        all_data: list[ZLMDataRow] | list[dict[str, Any]],
    ) -> float:
        """
        Calculate balloon height using official ZLM COPD scoring guide.
        Based on ccq-copd-questionnaire.md documentation.

        Args:
            domain_name: Name of the domain (e.g., "Long klachten", "Vermoeidheid")
            score: The score for this domain (0-6)
            all_data: All domain data (needed for cross-domain checks)

        Returns:
            Balloon height as percentage (0-100%)
        """
        if score is None:
            return 0.0

        # Domain-specific scoring logic from official ZLM COPD documentation
        if domain_name in ["Long aanvallen", "Longaanvallen", "Longaanval"]:
            # G17: Enhanced graduated scoring for exacerbations (0-4 scale → 0-100% height)
            # More gradation to use full balloon height range
            if score <= 0.5:  # 0 kuren
                return 100.0  # Green (perfect, no exacerbations)
            elif score <= 1.5:  # 1 kuur
                return 75.0  # Light green/orange (mild concern)
            elif score <= 2.5:  # 2 kuren
                return 50.0  # Orange (moderate concern)
            elif score <= 3.5:  # 3 kuren
                return 25.0  # Dark orange/red (serious concern)
            else:  # 4+ kuren
                return 0.0  # Red (critical concern)

        elif domain_name in ["Longklachten", "Long klachten", "Longklacht"]:
            # CRITICAL: Longklachten requires G12 check (kortademig in rust)
            # Official rule: Score < 1 AND G12 < 2 = Green, Score ≥1-≤2 AND G12 < 2 = Orange, Score > 2 OR G12 ≥ 2 = Red

            # Try to find G12 value in all_data
            g12_value = None
            try:
                if isinstance(all_data, list) and len(all_data) > 0:
                    for item in all_data:
                        if isinstance(item, dict):
                            # Look for G12 related domain
                            x_val = str(item.get("x_value", "")).lower()
                            if any(
                                keyword in x_val
                                for keyword in ["kortademig", "rust", "g12"]
                            ):
                                # Found potential G12 item, extract its y_current score
                                if "y_current" in item:
                                    g12_value = float(item["y_current"])
                                    break
                        elif hasattr(item, "x_value") and hasattr(item, "y_current"):
                            # ZLMDataRow object
                            x_val = str(item.x_value).lower()
                            if any(
                                keyword in x_val
                                for keyword in ["kortademig", "rust", "g12"]
                            ):
                                g12_value = float(item.y_current)
                                break
            except (ValueError, TypeError, AttributeError):
                # If we can't extract G12, fall back to general scoring
                pass

            # Apply official Longklachten scoring with G12 check
            if g12_value is not None:
                # Official logic with G12 check
                if score < 1.0 and g12_value < 2.0:
                    # Groen: BallonHoogte(%) = 100 - (Score * 20)
                    height = 100.0 - (score * 20.0)
                    return max(0.0, min(100.0, height))
                elif score >= 1.0 and score <= 2.0 and g12_value < 2.0:
                    # Oranje: BallonHoogte(%) = 80 - ((Score - 1) * 20)
                    height = 80.0 - ((score - 1.0) * 20.0)
                    return max(0.0, min(100.0, height))
                else:  # score > 2.0 OR g12_value >= 2.0
                    # Rood: BallonHoogte(%) = 40 - ((Score - 2) / 4 * 40)
                    height = 40.0 - ((score - 2.0) / 4.0 * 40.0)
                    return max(0.0, min(100.0, height))
            else:
                # Fallback: Use general scoring if G12 not found
                # This should not happen in production but provides safety
                pass  # Fall through to general scoring

        elif domain_name in ["Gewicht (BMI)", "Gewicht", "BMI", "Weight"]:
            # CRITICAL: BMI scoring uses direct BMI ranges, not 0-6 scale conversion
            # Official ranges from ccq-copd-questionnaire.md:
            # ≥21 en <25: Groen (100%)
            # ≥25 en <35: Oranje (20-80%), lineair geschaald
            # ≥18.5 en <21: Oranje (70-<100%), lineair geschaald
            # ≥35: Rood (0%)
            # <18.5: Rood (0%)

            # Try to extract BMI value or calculate from weight/height
            bmi_value = None

            # Method 1: BMI might be passed directly as the score
            if score is not None and 10.0 <= score <= 60.0:  # Reasonable BMI range
                bmi_value = score

            # Method 2: Try to find weight and height in all_data to calculate BMI
            if bmi_value is None:
                try:
                    weight_kg = None
                    height_cm = None

                    if isinstance(all_data, list):
                        for item in all_data:
                            if isinstance(item, dict):
                                x_val = str(item.get("x_value", "")).lower()
                                if any(
                                    keyword in x_val
                                    for keyword in ["gewicht", "weight", "g21"]
                                ):
                                    if "y_current" in item:
                                        weight_kg = float(item["y_current"])
                                elif any(
                                    keyword in x_val
                                    for keyword in ["lengte", "height", "g22"]
                                ):
                                    if "y_current" in item:
                                        height_cm = float(item["y_current"])
                            elif hasattr(item, "x_value") and hasattr(
                                item, "y_current"
                            ):
                                x_val = str(item.x_value).lower()
                                if any(
                                    keyword in x_val
                                    for keyword in ["gewicht", "weight", "g21"]
                                ):
                                    weight_kg = float(item.y_current)
                                elif any(
                                    keyword in x_val
                                    for keyword in ["lengte", "height", "g22"]
                                ):
                                    height_cm = float(item.y_current)

                    # Calculate BMI if both weight and height found
                    if (
                        weight_kg is not None
                        and height_cm is not None
                        and height_cm > 0
                    ):
                        height_m = height_cm / 100.0
                        bmi_value = weight_kg / (height_m * height_m)

                except (ValueError, TypeError, AttributeError, ZeroDivisionError):
                    pass

            # Apply official BMI scoring
            if bmi_value is not None:
                if bmi_value >= 21.0 and bmi_value < 25.0:
                    # Groen (100%)
                    return 100.0
                elif bmi_value >= 25.0 and bmi_value < 35.0:
                    # Oranje (20-80%), lineair geschaald
                    # Linear scaling: BMI 25 → 80%, BMI 35 → 20%
                    height = 80.0 - ((bmi_value - 25.0) / 10.0 * 60.0)
                    return max(20.0, min(80.0, height))
                elif bmi_value >= 18.5 and bmi_value < 21.0:
                    # Oranje (70-<100%), lineair geschaald
                    # Linear scaling: BMI 18.5 → 70%, BMI 21 → 100%
                    height = 70.0 + ((bmi_value - 18.5) / 2.5 * 30.0)
                    return max(70.0, min(100.0, height))
                elif bmi_value >= 35.0:
                    # Rood (0%) - Ernstig overgewicht
                    return 0.0
                elif bmi_value < 18.5:
                    # Rood (0%) - Ondergewicht
                    return 0.0
                else:
                    # Edge case fallback
                    return 50.0
            else:
                # Fallback: if BMI cannot be determined, use general scoring
                pass  # Fall through to general scoring

        elif domain_name == "Bewegen":
            # G18: Exercise days per week - OFFICIAL INVERTED SCORING
            # CRITICAL: G18 gets inverted in ZLMuitslag role conversion:
            # G18=0 dagen → ZLM Score=6, G18=1-2 dagen → ZLM Score=4,
            # G18=3-4 dagen → ZLM Score=2, G18=5+ dagen → ZLM Score=0
            # After inversion, LOWER ZLM score = MORE exercise days = HIGHER balloon

            # Official balloon heights based on exercise frequency:
            # 5+ dagen (score=0): Groen (100%)
            # 3-4 dagen (score=2): Oranje (60%)
            # 1-2 dagen (score=4): Oranje (40%)
            # 0 dagen (score=6): Rood (0%)

            if score <= 0.5:  # Score 0 = 5+ dagen beweging (na inversie)
                return 100.0  # Green - beweegt voldoende
            elif score <= 2.5:  # Score 2 = 3-4 dagen beweging (na inversie)
                return 60.0  # Orange - stap in goede richting
            elif score <= 4.5:  # Score 4 = 1-2 dagen beweging (na inversie)
                return 40.0  # Orange - beweegt, maar nog niet genoeg
            else:  # Score 6 = 0 dagen beweging (na inversie)
                return 0.0  # Red - beweegt onvoldoende

        elif domain_name == "Alcohol":
            # G19: Alcohol glasses per week - OFFICIAL DIRECT MAPPING
            # Official ranges from ccq-copd-questionnaire.md:
            # 0 glazen: Groen (100%)
            # 1-7 glazen: Oranje (60%)
            # 8-14 glazen: Oranje (40%)
            # 14+ glazen: Rood (0%)

            # Score represents G19 answer value (0-3 scale in questionnaire)
            # G19 mapping: 0=0 glazen, 1=1-7 glazen, 2=8-14 glazen, 3=15+ glazen
            if score <= 0.5:  # G19=0 (0 glazen)
                return 100.0  # Green
            elif score <= 1.5:  # G19=1 (1-7 glazen)
                return 60.0  # Orange
            elif score <= 2.5:  # G19=2 (8-14 glazen)
                return 40.0  # Orange
            else:  # G19=3 (15+ glazen)
                return 0.0  # Red

        elif domain_name == "Roken":
            # G20: Smoking status - OFFICIAL DIRECT MAPPING
            # Official ranges from ccq-copd-questionnaire.md:
            # Nooit gerookt: Groen (100%)
            # Vroeger gerookt: Groen (100%) (Note: limited granularity in G20)
            # Ja (rookt): Rood (0%)

            # Score represents G20 answer mapping
            # G20 mapping: 'nooit'→0, 'vroeger'→1, 'ja'→6 (from ZLMuitslag conversion)
            # Also handle string values directly in case conversion hasn't happened yet
            if isinstance(score, str):
                if score.lower() in ["nooit", "never"]:
                    return 100.0  # Green
                elif score.lower() in ["vroeger", "former"]:
                    return 100.0  # Green
                else:  # 'ja', 'yes', or any other value
                    return 0.0  # Red

            # Handle numeric scores
            if score <= 0.5:  # G20='nooit' (never smoked)
                return 100.0  # Green
            elif score <= 1.5:  # G20='vroeger' (former smoker)
                return 100.0  # Green (official says 100% for former smokers)
            else:  # G20='ja' (current smoker)
                return 0.0  # Red

        # OFFICIAL GENERAL SCORING - Based on ccq-copd-questionnaire.md lineaire schaling
        # These formulas replace the previous complex scoring logic

        # Voor Groene ballonnen (scores < 1):
        # BallonHoogte(%) = 100 - (Score * 20)
        if score < 1.0:
            height = 100.0 - (score * 20.0)
            return max(0.0, min(100.0, height))  # Clamp between 0-100%

        # Voor Oranje ballonnen (scores 1-2):
        # BallonHoogte(%) = 80 - ((Score - 1) * 20)
        elif score <= 2.0:
            height = 80.0 - ((score - 1.0) * 20.0)
            return max(0.0, min(100.0, height))  # Clamp between 0-100%

        # Voor Rode ballonnen (scores > 2):
        # BallonHoogte(%) = 40 - ((Score - 2) / 4 * 40)
        else:  # score > 2.0
            height = 40.0 - ((score - 2.0) / 4.0 * 40.0)
            return max(0.0, min(100.0, height))  # Clamp between 0-100%

    def _substitute_double_curly_placeholders(
        self, template_string: str, data_dict: dict[str, Any]
    ) -> str:
        """Substitutes {{placeholder}} style placeholders in a string with values from data_dict."""

        # First, replace all known placeholders
        output_string = template_string
        for key, value in data_dict.items():
            placeholder = "{{" + key + "}}"
            output_string = output_string.replace(placeholder, str(value))

        # Then, find any remaining {{...}} placeholders that were not in data_dict
        # and replace them with a [missing:key_name] indicator.
        # This mimics the DefaultKeyDict behavior for unprovided keys.
        def replace_missing_with_indicator(match: re.Match[str]) -> str:
            var_name = match.group(1)  # Content inside {{...}}
            return f"[missing:{var_name}]"

        output_string = re.sub(
            r"\{\{([^}]+)\}\}", replace_missing_with_indicator, output_string
        )
        return output_string

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam], _: int = 0
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        # Get the current role
        role_config = await self.get_current_role()

        # Get the available tools
        tools = self.get_tools()

        # Filter tools based on the role's regex pattern
        tools_values = [
            tool
            for tool in tools.values()
            if re.match(role_config.tools_regex, tool.__name__)
            or tool.__name__ == BaseTools.tool_noop.__name__
            or tool.__name__ == BaseTools.tool_call_super_agent.__name__
        ]

        # Prepare questionnaire format kwargs
        questionnaire_format_kwargs: dict[str, str] = {}
        for q_item in role_config.questionaire:
            answer = await self.get_metadata(q_item.name, "[not answered]")
            questionnaire_format_kwargs[f"questionaire_{q_item.name}_question"] = (
                q_item.question
            )
            questionnaire_format_kwargs[f"questionaire_{q_item.name}_instructions"] = (
                q_item.instructions
            )
            questionnaire_format_kwargs[f"questionaire_{q_item.name}_name"] = (
                q_item.name
            )
            questionnaire_format_kwargs[f"questionaire_{q_item.name}_answer"] = answer

        # Format the role prompt with questionnaire data
        try:
            formatted_current_role_prompt = self._substitute_double_curly_placeholders(
                role_config.prompt, questionnaire_format_kwargs
            )
        except Exception as e:
            self.logger.warning(f"Error formatting role prompt: {e}")
            formatted_current_role_prompt = role_config.prompt

        # Gather reminders and recurring tasks
        recurring_tasks = await self.get_metadata("recurring_tasks", [])
        reminders = await self.get_metadata("reminders", [])
        memories = await self.get_metadata("memories", [])
        notifications = await self.get_metadata("notifications", [])

        # Prepare the main content for the LLM
        main_prompt_format_args = {
            "current_role": role_config.name,
            "current_role_prompt": formatted_current_role_prompt,
            "available_roles": "\n".join(
                [f"- {role.name}" for role in self.config.roles]
            ),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "recurring_tasks": "\n".join(
                [
                    f"- {task['id']}: {task['cron_expression']} - {task['task']}"
                    for task in recurring_tasks
                ]
            )
            if recurring_tasks
            else "<no recurring tasks>",
            "reminders": "\n".join(
                [
                    f"- {reminder['id']}: {reminder['date']} - {reminder['message']}"
                    for reminder in reminders
                ]
            )
            if reminders
            else "<no reminders>",
            "memories": "\n".join(
                [f"- {memory['id']}: {memory['memory']}" for memory in memories]
            )
            if memories
            else "<no memories>",
            "notifications": "\n".join(
                [
                    f"{notification.get('id')}: {notification.get('contents')} at {notification.get('sent_at')}"
                    for notification in notifications
                ]
            )
            if notifications
            else "<no notifications>",
            "metadata": json.dumps((await self._get_thread()).metadata),
        }
        main_prompt_format_args.update(questionnaire_format_kwargs)

        # Store session metadata from headers
        onesignal_id = self.request_headers.get("x-onesignal-external-user-id")
        assistant_field_name = self.request_headers.get("x-assistant-field-name")

        if onesignal_id is not None:
            await self.set_metadata("onesignal_id", onesignal_id)

        if assistant_field_name is not None:
            await self.set_metadata("assistant_field_name", assistant_field_name)

        try:
            llm_content = self._substitute_double_curly_placeholders(
                self.config.prompt, main_prompt_format_args
            )
        except Exception as e:
            self.logger.warning(f"Error formatting system prompt: {e}")
            llm_content = (
                f"Role: {role_config.name}\nPrompt: {formatted_current_role_prompt}"
            )

        self.logger.debug(llm_content)

        # Create the completion request
        response = await self.client.chat.completions.create(
            model=role_config.model,
            messages=[
                {
                    "role": "system",
                    "content": llm_content,
                },
                *messages,
            ],
            stream=True,
            tools=[function_to_openai_tool(tool) for tool in tools_values],
            tool_choice="auto",
        )

        return response, list(tools_values)

    @staticmethod
    def super_agent_config() -> SuperAgentConfig[MUMCAgentConfig] | None:
        return SuperAgentConfig(
            cron_expression="0 * * * *",  # every hour at 0 minutes past
            agent_config=MUMCAgentConfig(),
        )

    async def on_super_agent_call(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> (
        tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]] | None
    ):
        onesignal_id = await self.get_metadata("onesignal_id")

        if onesignal_id is None:
            self.logger.info("No onesignal id found, skipping super agent call")
            return

        last_thread = await prisma.threads.query_first(
            """
        SELECT * FROM threads
        WHERE metadata->>'onesignal_id' = $1
        ORDER BY created_at DESC
        LIMIT 1
        """,
            onesignal_id,
        )

        if last_thread is None:
            self.logger.info("No last thread found, skipping super agent call")
            return

        if last_thread.id != self.thread_id:
            self.logger.info(
                "Last thread id does not match current thread id, skipping super agent call"
            )
            return

        tools = [
            BaseTools.tool_noop,
            self.get_tools()["tool_send_notification"],
        ]

        notifications = await self.get_metadata("notifications", [])
        reminders = await self.get_metadata("reminders", [])
        recurring_tasks = await self.get_metadata("recurring_tasks", [])

        prompt = f"""
# Notification Management System

## Core Responsibility
You are the notification management system responsible for delivering timely alerts without duplication. Your task is to analyze pending notifications and determine which ones need to be sent.

## Current Time
Current system time: {datetime.now(pytz.timezone("Europe/Amsterdam")).strftime("%Y-%m-%d %H:%M:%S")}

## Previously Sent Notifications
The following notifications have already been sent and MUST NOT be resent:
{json.dumps(notifications, indent=2)}

## Items to Evaluate
Please evaluate these items for notification eligibility:

1. Reminders:
{json.dumps(reminders, indent=2)}

2. Recurring Tasks:
{json.dumps(recurring_tasks, indent=2)}

## Decision Rules
- A notification should be sent for any reminder that is currently due
- For recurring tasks, evaluate the cron expression to determine if it should be triggered at the current time
- If a cron expression indicates the task is due now and hasn't already been sent today, send a notification
- If an item appears in the previously sent notifications list, it MUST be skipped
- Parse cron expressions carefully to determine exact scheduling (minute, hour, day of month, month, day of week)
- The date attribute of the reminders in the reminders list is the due date. If that date is before the current date, the reminder is due.

## Required Action
After analysis, you must take exactly ONE of these actions:
- If any eligible notifications are found: invoke the send_notification tool with details
- If no eligible notifications exist: invoke the noop tool
"""

        self.logger.info(f"Calling super agent with prompt: {prompt}")

        response = await self.client.chat.completions.create(
            model="openai/gpt-4.1",  # Consider making this configurable or same as role_config.model
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": "Send my notifications",
                },
            ],
            tools=[function_to_openai_tool(tool) for tool in tools],
            tool_choice="auto",
        )

        self.logger.info(f"Super agent response: {response.choices[0].message}")

        async for _ in self._handle_completion(response, tools, messages):
            pass
