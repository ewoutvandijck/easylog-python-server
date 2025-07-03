import io
import re
import uuid
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any, Literal

import httpx
from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from PIL import Image, ImageOps
from prisma.enums import health_data_point_type
from prisma.types import health_data_pointsWhereInput, usersWhereInput
from pydantic import BaseModel, Field
from src.agents.base_agent import BaseAgent
from src.agents.tools.easylog_backend_tools import EasylogBackendTools
from src.agents.tools.easylog_sql_tools import EasylogSqlTools
from src.agents.tools.knowledge_graph_tools import KnowledgeGraphTools
from src.lib.prisma import prisma
from src.models.chart_widget import (
    DEFAULT_COLOR_ROLE_MAP,
    ChartWidget,
    Line,
    ZLMDataRow,
)
from src.models.multiple_choice_widget import Choice, MultipleChoiceWidget
from src.settings import settings
from src.utils.function_to_openai_tool import function_to_openai_tool


class RoleConfig(BaseModel):
    name: str = Field(default="James")
    prompt: str = Field(default="You are a helpful assistant.")
    model: str = Field(default="openai/gpt-4.1")
    tools_regex: str = Field(default=".*")


class RickThropicAgentConfig(BaseModel):
    roles: list[RoleConfig] = Field(
        default_factory=lambda: [
            RoleConfig(
                name="James",
                prompt="You are a helpful assistant.",
                model="openai/gpt-4.1",
                tools_regex=".*",
            )
        ]
    )
    prompt: str = Field(
        default="You can use the following roles: {available_roles}. You are currently using the role: {current_role}. Your prompt is: {current_role_prompt}. You can use the following recurring tasks: {recurring_tasks}. You can use the following reminders: {reminders}. The current time is: {current_time}."
    )


class CarEntity(BaseModel):
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    horsepower: int | None = None
    color: str | None = None
    price: int | None = None


class PersonEntity(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    birth_date: str | None = None
    gender: str | None = None


class JobEntity(BaseModel):
    title: str | None = None
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class RickThropicAgent(BaseAgent[RickThropicAgentConfig]):
    def get_tools(self) -> list[Callable]:
        easylog_token = self.request_headers.get("x-easylog-bearer-token", "")
        easylog_backend_tools = EasylogBackendTools(
            bearer_token=easylog_token,
            base_url=settings.EASYLOG_API_URL,
        )

        if easylog_token:
            self.logger.debug(f"credentials='{easylog_token}'")

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

        knowledge_graph_tools = KnowledgeGraphTools(
            entities={"Car": CarEntity, "Person": PersonEntity, "Job": JobEntity},
        )

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

        def tool_create_zlm_chart(
            language: Literal["nl", "en"],
            data: list[ZLMDataRow],
        ) -> ChartWidget:
            """
            Creates a ZLM (Ziektelastmeter COPD) balloon chart using a predefined ZLM color scheme.
            The chart visualizes scores, expecting values in the 0-10 range. Where 0 is bad and 10 is the best
            The y-axis label is derived from the `y_label` field of the first data item.

            Args:
                language: The language for chart title and description ('nl' or 'en').
                data: A list of `ZLMDataRow` objects for the chart. Each item represents a
                      category on the x-axis and its corresponding scores.
                      - `x_value` (str): The name of the category (e.g., "Algemeen").
                      - `y_current` (float): The current score (0-10).
                      - `y_old` (float | None): Optional. The previous score the patient had (0-10).
                      - `y_label` (str): The label for the y-axis, typically including units
                                         (e.g., "Score (0-10)"). This is used for the overall
                                         Y-axis label of the chart.

            Returns:
                A ChartWidget object configured as a balloon chart.

            Raises:
                ValueError: If the `data` list is empty.

            Example:
                ```python
                # Assuming ZLMDataRow is imported from src.models.chart_widget
                data = [
                    ZLMDataRow(x_value="Physical pain", y_current=7.5, y_old=6.0, y_label="Score (0-10)"),
                    ZLMDataRow(x_value="Mental health", y_current=8.2, y_old=8.5, y_label="Score (0-10)"),
                    ZLMDataRow(x_value="Social support", y_current=3.0, y_label="Schaal (0-5)"),  # No old value
                ]
                chart_widget = tool_create_zlm_chart(language="nl", data=data)
                ```
            """
            # TODO: We should calculate colors for domains based linearly, and include exceptions for relevant domains.

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

            # Check that data list is at least 1 or more,.
            if len(data) < 1:
                raise ValueError("Data list must be at least 1 or more.")

            # Convert dictionaries to ZLMDataRow objects if needed
            return ChartWidget.create_balloon_chart(
                title=title,
                description=description,
                data=data,
            )

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

            print("No steps data found for user between", date_from, "and", date_to)

            if not steps_data:
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
                {"created_at": step.created_at.isoformat(), "value": step.value}
                for step in steps_data
            ]

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
            f"""
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
            *easylog_backend_tools.all_tools,
            *easylog_sql_tools.all_tools,
            *knowledge_graph_tools.all_tools,
            tool_set_current_role,
            tool_download_image,
            tool_set_recurring_task,
            tool_remove_recurring_task,
            tool_add_reminder,
            tool_remove_reminder,
            tool_ask_multiple_choice,
            tool_create_bar_chart,
            tool_create_zlm_chart,
            tool_create_line_chart,
            tool_get_steps_data,
            tool_get_date_time,
        ]

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam], _: int = 0
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        role = await self.get_metadata("current_role", self.config.roles[0].name)
        if role not in [role.name for role in self.config.roles]:
            role = self.config.roles[0].name

        role_config = next(
            role_config for role_config in self.config.roles if role_config.name == role
        )

        tools = self.get_tools()

        for tool in tools:
            self.logger.info(f"{tool.__name__}: {tool.__doc__}")

        tools = [
            tool for tool in tools if re.match(role_config.tools_regex, tool.__name__)
        ]

        recurring_tasks = await self.get_metadata("recurring_tasks", [])
        reminders = await self.get_metadata("reminders", [])

        response = await self.client.chat.completions.create(
            model=role_config.model,
            messages=[
                {
                    "role": "developer",
                    "content": self.config.prompt.format(
                        current_role=role,
                        current_role_prompt=role_config.prompt,
                        available_roles="\n".join(
                            [
                                f"- {role.name}: {role.prompt}"
                                for role in self.config.roles
                            ]
                        ),
                        recurring_tasks="\n".join(
                            [
                                f"- {task['id']}: {task['cron_expression']} - {task['task']}"
                                for task in recurring_tasks
                            ]
                        ),
                        reminders="\n".join(
                            [
                                f"- {reminder['id']}: {reminder['date']} - {reminder['message']}"
                                for reminder in reminders
                            ]
                        ),
                        current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                },
                *messages,
            ],
            stream=True,
            tools=[function_to_openai_tool(tool) for tool in tools],
            tool_choice="auto",
        )

        return response, tools
