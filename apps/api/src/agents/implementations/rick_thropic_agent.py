import io
import re
import uuid
from collections.abc import Callable, Iterable
from datetime import datetime, time
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
    ChartWidget,
    ZLMDataRow,
)
from src.models.multiple_choice_widget import Choice, MultipleChoiceWidget
from src.settings import settings
from src.utils.function_to_openai_tool import function_to_openai_tool
from src.agents.tools.parse_horizontal_lines import parse_horizontal_lines


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


class ZLMQuestionnaireAnswers(BaseModel):
    """Validated answers for the Ziektelastmeter COPD questionnaire (G1–G22)."""

    G1: int = Field(..., ge=0, le=6)
    G2: int = Field(..., ge=0, le=6)
    G3: int = Field(..., ge=0, le=6)
    G4: int = Field(..., ge=0, le=6)
    G5: int = Field(..., ge=0, le=6)
    G6: int = Field(..., ge=0, le=6)
    G7: int = Field(..., ge=0, le=6)
    G8: int = Field(..., ge=0, le=6)
    G9: int = Field(..., ge=0, le=6)
    G10: int = Field(..., ge=0, le=6)
    G11: int = Field(..., ge=0, le=6)
    G12: int = Field(..., ge=0, le=6)
    G13: int = Field(..., ge=0, le=6)
    G14: int = Field(..., ge=0, le=6)
    G15: int = Field(..., ge=0, le=6)
    G16: int = Field(..., ge=0, le=6)
    G17: int = Field(..., ge=0, le=4)
    G18: int = Field(..., ge=0, le=6)
    G19: int = Field(..., ge=0, le=6)
    G20: Literal["nooit", "vroeger", "ja"]
    G21: float = Field(..., gt=0)
    G22: float = Field(..., gt=0)


# ---------------------------------------------------------------------------
# Helper types
# ---------------------------------------------------------------------------


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

        # ------------------------------------------------------------------
        # Questionnaire utilities
        # ------------------------------------------------------------------

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
            """Retrieve a previously stored questionnaire answer.

            Args:
                question_name: The name/identifier of the questionnaire question (e.g. "g1").

            Returns
            -------
            str
                The stored answer or the string "[not answered]" when no answer is found.
            """

            return await self.get_metadata(question_name, "[not answered]")

        async def tool_store_memory(memory: str) -> str:
            """Persist a memory string in the agent context.

            Args:
                memory: The memory text to store.

            Returns
            -------
            str
                Confirmation message.
            """

            memories = await self.get_metadata("memories", [])
            memories.append({"id": str(uuid.uuid4())[0:8], "memory": memory})
            await self.set_metadata("memories", memories)

            return f"Memory stored: {memory}"

        # ------------------------------------------------------------------
        # ZLM score calculation
        # ------------------------------------------------------------------

        async def tool_calculate_zlm_scores() -> dict[str, float]:
            """Calculate Ziektelastmeter COPD domain scores based on previously
            answered questionnaire values. The questionnaire must be complete before calling this tool.

            Upon successful calculation the individual domain scores **and** the
            calculated BMI value are persisted as memories using
            ``tool_store_memory``.
            """

            # --------------------------------------------------------------
            # 1. Gather & validate answers
            # --------------------------------------------------------------
            question_codes = [f"G{i}" for i in range(1, 23)]  # g1 … g22 inclusive

            raw_answers: dict[str, str] = {}
            missing: list[str] = []
            for code in question_codes:
                ans = await tool_get_questionaire_answer(code)
                if ans in {"[not answered]", None, ""}:
                    missing.append(code)
                else:
                    raw_answers[code] = ans

            if missing:
                raise ValueError(
                    "Missing questionnaire answers for: " + ", ".join(missing)
                )

            # --------------------------------------------------------------
            # 2. Parse & validate using Pydantic model
            # --------------------------------------------------------------
            def _to_int(val: str) -> int:
                try:
                    return int(val)
                except Exception as exc:
                    raise ValueError(
                        f"Expected integer, got '{val}' for question."
                    ) from exc

            def _to_float(val: str) -> float:
                try:
                    return float(val)
                except Exception as exc:
                    raise ValueError(
                        f"Expected float, got '{val}' for question."
                    ) from exc

            parsed: dict[str, Any] = {
                # ints 0-6 unless specified
                **{
                    f"G{i}": _to_int(raw_answers[f"G{i}"])
                    for i in range(1, 20)
                    if i != 20
                },
                # g20 remains str literal
                "G20": raw_answers["G20"].strip().lower(),
                # floats
                "G21": _to_float(raw_answers["G21"]),
                "G22": _to_float(raw_answers["G22"]),
            }

            answers = ZLMQuestionnaireAnswers(**parsed)

            # --------------------------------------------------------------
            # 3. Domain score computation
            # --------------------------------------------------------------
            from statistics import mean

            def _avg(vals: list[int]) -> float:
                return float(mean(vals)) if vals else 0.0

            scores: dict[str, float] = {
                "longklachten": _avg(
                    [answers.G12, answers.G13, answers.G15, answers.G16]
                ),
                "longaanvallen": float(answers.G17),
                "lichamelijke_beperkingen": _avg([answers.G5, answers.G6, answers.G7]),
                "vermoeidheid": float(answers.G1),
                "nachtrust": float(answers.G2),
                "gevoelens_emoties": _avg([answers.G3, answers.G11, answers.G14]),
                "seksualiteit": float(answers.G10),
                "relaties_en_werk": _avg([answers.G8, answers.G9]),
                "medicijnen": float(answers.G4),
                "bewegen": float(answers.G18),
                "alcohol": float(answers.G19),
            }

            # BMI-related score
            height_m = answers.G22 / 100.0
            bmi_value = answers.G21 / (height_m**2)
            if bmi_value < 16:
                gewicht_score = 4
            elif bmi_value < 18.5:
                gewicht_score = 2
            elif bmi_value < 25:
                gewicht_score = 0
            elif bmi_value < 30:
                gewicht_score = 2
            elif bmi_value < 35:
                gewicht_score = 4
            else:
                gewicht_score = 6

            scores["gewicht_bmi"] = float(gewicht_score)

            # Scale scores that are not already 0-6 to 0-6
            scores["longaanvallen"] = scores["longaanvallen"] * 1.5
            # score 0-3 to 0-6

            # Roken score
            roken_map = {"nooit": 0, "vroeger": 2, "ja": 6}
            scores["roken"] = float(roken_map[answers.G20])

            # --------------------------------------------------------------
            # 4. Persist memories
            # --------------------------------------------------------------
            label_map = {
                "longklachten": "Longklachten",
                "longaanvallen": "Longaanvallen",
                "lichamelijke_beperkingen": "Lichamelijke-beperkingen",
                "vermoeidheid": "Vermoeidheid",
                "nachtrust": "Nachtrust",
                "gevoelens_emoties": "Emoties",
                "seksualiteit": "Seksualiteit",
                "relaties_en_werk": "Relaties-en-werk",
                "medicijnen": "Medicijnen",
                "gewicht_bmi": "BMI",
                "bewegen": "Bewegen",
                "alcohol": "Alcohol",
                "roken": "Roken",
            }

            today_str = datetime.now().strftime("%d-%m-%Y")

            # Store domain scores
            for key, score in scores.items():
                label = label_map.get(key, key.title())
                mem = f"ZLM-Score-{label} {today_str}: Score = {score}"
                await tool_store_memory(mem)

            mem = f"ZLM-BMI-meta_value {today_str} {bmi_value}"
            await tool_store_memory(mem)

            return scores

        def tool_create_zlm_chart(
            language: Literal["nl", "en"],
            data: list[ZLMDataRow],
        ) -> ChartWidget:
            """
            Creates a ZLM (Ziektelastmeter COPD) balloon chart using a predefined ZLM color scheme.
            The chart visualizes scores, expecting values in the 0-6 range. Where 0 is good and 6 is the worst
            The y-axis label is derived from the `y_label` field of the first data item.

            Args:
                language: The language for chart title and description ('nl' or 'en').
                data: A list of `ZLMDataRow` objects for the chart. Each item represents a
                      category on the x-axis and its corresponding scores.
                      - `x_value` (str): The name of the category (e.g., "Algemeen").
                      - `y_current` (float): The current score (0-6).
                      - `y_old` (float | None): Optional. The previous score the patient had (0-6).
                      - `y_label` (str): The label for the y-axis, typically including units
                                         (e.g., "Score (0-6)"). This is used for the overall
                                         Y-axis label of the chart.
                      - `meta` (str | None): Optional. Extra information for this data point shown to the user. Add the BMI value here for the BMI score data point.

            Returns:
                A ChartWidget object configured as a balloon chart.

            Raises:
                ValueError: If the `data` list is empty.

            Example:
                ```python
                # Assuming ZLMDataRow is imported from src.models.chart_widget
                data = [
                    ZLMDataRow(x_value="Physical pain", y_current=7.5, y_old=6.0, y_label="Score (0-6)"),
                    ZLMDataRow(x_value="Mental health", y_current=8.2, y_old=8.5, y_label="Score (0-6)"),
                    ZLMDataRow(x_value="Social support", y_current=3.0, y_label="Schaal (0-5)"),  # No old value
                ]
                chart_widget = tool_create_zlm_chart(language="nl", data=data)
                ```
            """

            title = (
                "Resultaten ziektelastmeter"
                if language == "nl"
                else "Disease burden results"
            )

            # Check that data list is at least 1 or more,.
            if len(data) < 1:
                raise ValueError("Data list must be at least 1 or more.")

            # Convert dictionaries to ZLMDataRow objects if needed
            return ChartWidget.create_balloon_chart(
                title=title,
                data=data,
            )

        async def tool_get_steps_data(
            date_from: str | datetime,
            date_to: str | datetime,
            timezone: str | None = None,
            aggregation: str | None = None,
        ) -> list[dict[str, Any]]:
            """Retrieve a user’s step counts with optional time aggregation.

            Parameters
            ----------
            date_from, date_to : str | datetime
                Inclusive ISO-8601 strings **or** ``datetime`` objects that define the
                query window in the *local* timezone (see ``timezone``).

            timezone : str | None, default ``"Europe/Amsterdam"``
                IANA timezone name used to interpret naïve datetimes **and** for the
                timestamps returned by this tool.

            aggregation : {"quarter", "hour", "day", None}, default ``day``
                • ``"quarter"`` → 15-minute buckets
                • ``"hour"``     → hourly totals
                • ``"day"``      → daily totals
                • ``None``/empty → **defaults to daily** (same as ``"day"``)

            The granularity increases from *quarter* (smallest) → *hour* → *day*.

            Returns
            -------
            list[dict[str, Any]]
                A list **capped at 300 rows**. Each item contains:
                ``created_at`` – ISO timestamp in requested timezone
                ``value`` – summed step count for the bucket (aggregated) **or** the
                original ``value`` plus ``date_from``/``date_to`` (raw mode).

            Notes
            -----
            • The result set is limited to **max 300 rows** to protect the UI and
              network usage. If the database returns more rows, only the first 300
              (ordered chronologically) are returned.
            """

            from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

            # ------------------------------------------------------------------ #
            # 0. Normalise / validate aggregation parameter                     #
            # ------------------------------------------------------------------ #
            agg_raw = (aggregation or "").strip().lower()

            if agg_raw in {"", "none"}:
                aggregation_normalised = "day"
            elif agg_raw in {"hour", "hourly"}:
                aggregation_normalised = "hour"
            elif agg_raw in {"day", "daily"}:
                aggregation_normalised = "day"
            elif agg_raw in {"quarter", "quarterly", "q", "15m", "15min", "15"}:
                aggregation_normalised = "quarter"
            else:
                raise ValueError(
                    "Invalid aggregation value. Use one of: 'quarter', 'hour', 'day', or None/empty."
                )

            aggregation = aggregation_normalised  # overwrite with canonical value

            # ------------------------------------------------------------------ #
            # 1. Resolve / validate timezone                                     #
            # ------------------------------------------------------------------ #
            tz_name = (timezone or "Europe/Amsterdam").strip()
            if tz_name in {"CET", "CEST"}:
                tz_name = "Europe/Amsterdam"

            try:
                tz = ZoneInfo(tz_name)
            except ZoneInfoNotFoundError as exc:
                raise ValueError(
                    f"Invalid timezone '{timezone}'. Please provide a valid IANA name."
                ) from exc

            UTC = ZoneInfo("UTC")  # single UTC instance for reuse

            # ------------------------------------------------------------------ #
            # 2. Parse inputs → timezone-aware datetimes                         #
            # ------------------------------------------------------------------ #
            def _parse_input(val: str | datetime) -> datetime:
                """ISO string → datetime; naïve → attach local tz."""
                dt_obj = datetime.fromisoformat(val) if isinstance(val, str) else val
                if dt_obj.tzinfo is None:  # treat naïve as local
                    dt_obj = dt_obj.replace(tzinfo=tz)
                return dt_obj

            date_from_dt = _parse_input(date_from)
            date_to_dt = _parse_input(date_to)

            extra = ""
            if date_from_dt.year < datetime.now().year:
                raise ValueError("Date from is in the past")

            # Expand “whole-day” range (00:00 → 23:59:59.999999)
            if (
                date_from_dt.date() == date_to_dt.date()
                and date_from_dt.timetz() == time(0, tzinfo=tz)
                and date_to_dt.timetz() == time(0, tzinfo=tz)
            ):
                date_to_dt = date_to_dt.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )

            # Convert to **UTC** for querying
            date_from_utc = date_from_dt.astimezone(UTC)
            date_to_utc = date_to_dt.astimezone(UTC)

            # ------------------------------------------------------------------ #
            # 3. Fetch user id                                                   #
            # ------------------------------------------------------------------ #
            external_user_id = self.request_headers.get("x-onesignal-external-user-id")
            if external_user_id is None:
                raise ValueError("User ID not provided and not found in agent context.")

            user = await prisma.users.find_first(
                where=usersWhereInput(external_id=external_user_id)
            )
            if user is None:
                raise ValueError("User not found")

            # ------------------------------------------------------------------ #
            # 4. Retrieve raw datapoints                                         #
            # ------------------------------------------------------------------ #
            steps_data = await prisma.health_data_points.find_many(
                where=health_data_pointsWhereInput(
                    user_id=user.id,
                    type=health_data_point_type.steps,
                    date_from={"gte": date_from_utc},
                    date_to={"lte": date_to_utc},
                ),
                order={"created_at": "asc"},
                take=300,
            )
            if not steps_data:
                return []

            # ------------------------------------------------------------------ #
            # 5. Helper: convert any str/naïve dt → ISO in *local* timezone      #
            # ------------------------------------------------------------------ #
            def _iso_local(val: str | datetime) -> str:
                dt_obj = datetime.fromisoformat(val) if isinstance(val, str) else val
                if dt_obj.tzinfo is None:  # DB can return naïve UTC
                    dt_obj = dt_obj.replace(tzinfo=UTC)
                return dt_obj.astimezone(tz).isoformat()

            # ------------------------------------------------------------------ #
            # 6. Aggregation                                                     #
            # ------------------------------------------------------------------ #
            if aggregation in {"hour", "day"}:
                rows: list[dict[str, Any]] = await prisma.query_raw(
                    f"""
                    SELECT
                        date_trunc('{aggregation}', date_from AT TIME ZONE 'UTC') AS bucket,
                        SUM(value)::int                                          AS total
                    FROM   health_data_points
                    WHERE  user_id  = $1::uuid
                    AND  type     = 'steps'
                    AND  date_from >= $2::timestamptz
                    AND  date_to   <= $3::timestamptz
                    GROUP  BY bucket
                    ORDER  BY bucket
                    LIMIT 300
                    """,
                    user.id,
                    date_from_utc,
                    date_to_utc,
                )

                return [
                    {
                        "created_at": _iso_local(row["bucket"]),
                        "value": row["total"],
                    }
                    for row in rows
                ]

            # ------------------------------------------------------------------ #
            # 6b. Quarter-hour aggregation                                       #
            # ------------------------------------------------------------------ #
            if aggregation == "quarter":
                from collections import defaultdict

                bucket_totals: dict[str, int] = defaultdict(int)

                for dp in steps_data:
                    start_dt = _parse_input(dp.date_from)
                    local_dt = start_dt.astimezone(tz)
                    floored_minute = (local_dt.minute // 15) * 15
                    bucket_dt = local_dt.replace(
                        minute=floored_minute, second=0, microsecond=0
                    )
                    bucket_key = bucket_dt.isoformat()
                    bucket_totals[bucket_key] += dp.value

                sorted_rows = sorted(bucket_totals.items())[:300]

                return [
                    {"created_at": key, "value": total} for key, total in sorted_rows
                ]

            # ------------------------------------------------------------------ #
            # 7. Raw datapoints                                                  #
            # ------------------------------------------------------------------ #
            return [
                {
                    "created_at": _iso_local(dp.created_at),
                    "date_from": _iso_local(dp.date_from),
                    "date_to": _iso_local(dp.date_to),
                    "value": dp.value,
                }
                for dp in steps_data
            ]

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

            ### Chart with Color Coding:
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

            Common mistakes:
                - x_key is not a string
                - y_keys are not strings
            """
            # ------------------------------------------------------------------
            # Validate / coerce custom_color_role_map
            # ------------------------------------------------------------------

            if horizontal_lines is not None:
                parsed_horizontal_lines = parse_horizontal_lines(horizontal_lines)
            else:
                parsed_horizontal_lines = None

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
            horizontal_lines: list[dict[str, Any]] | None = None,
            description: str | None = None,
            height: int = 400,
            y_axis_domain_min: float | None = None,
            y_axis_domain_max: float | None = None,
        ) -> ChartWidget:
            """Create a line chart with time series or continuous data visualization.

            • Line charts use automatic color assignment for each line series
            • Data points can have null values for missing data (creates gaps in lines)
            • Lines connect data points in the order they appear in the data array

            ## Data Structure Requirements

            The `data` parameter expects a list of dictionaries where:
            - Each dictionary represents one data point on the x-axis
            - The `x_key` field contains the x-axis value (typically string for dates/categories)
            - Each `y_key` field contains the numerical value for that data point
            - Missing data can be represented as `null` or omitted entirely

            ### Simple Time Series Example:
            data = [
                {"date": "2024-01-01", "temperature": 22.5, "humidity": 65},
                {"date": "2024-01-03", "temperature": 21.8, "humidity": null},  # Missing humidity
            ]

            ## Line Colors

            Line colors are automatically assigned using a default color palette:
            - First line: Blue (#007bff)
            - Second line: Green (#28a745) 
            - Third line: Orange (#fd7e14)
            - Additional lines continue with varied colors

            **Important:** Do not include color information in the data objects - colors are handled automatically.

            ## Horizontal Lines

            The `horizontal_lines` parameter accepts a list of dictionaries, each defining a reference line:
            ```python
            horizontal_lines = [
                {"value": 20000, "label": "Sales Target", "color": "#e8f5e8"},
                {"value": 10000},  # Just value, will use default label and color
            ]
            ```

            Required fields:
            - `value` (float): The y-axis value where the line is drawn

            Optional fields:
            - `label` (str): Text label for the line (defaults to None)
            - `color` (str): HEX color code (defaults to black)

            ## Complete Usage Examples

            ### Sales Performance Tracking:
            chart = tool_create_line_chart(
                title="Quarterly Sales Performance",
                data=[
                    {"month": "Q1", "revenue": 125000, "costs": 85000, "profit": 40000},
                    {"month": "Q2", "revenue": 142000, "costs": 92000, "profit": 50000},
                    {"month": "Q3", "revenue": 138000, "costs": 88000, "profit": 50000},
                    {"month": "Q4", "revenue": 156000, "costs": 98000, "profit": 58000},
                ],
                x_key="month",
                y_keys=["revenue", "costs", "profit"],
                horizontal_lines=[
                    {"value": 150000, "label": "Revenue Target", "color": "#d1ecf1"},
                    {"value": 45000, "label": "Profit Goal", "color": "#d4edda"},
                ],
                y_axis_domain_min=0,
                y_axis_domain_max=170000,
                height=500,
            )

            Args:
                title (str): The main title displayed above the chart.

                data (list[dict[str, Any]]): List of data objects. Each object represents one
                    data point on the x-axis. See examples above for structure.

                x_key (str): The dictionary key that contains the x-axis values
                    (e.g., "date", "month", "time").

                y_keys (list[str]): List of dictionary keys for the data series to plot as lines.
                    Each key becomes a separate line series (e.g., ["temperature", "humidity"]).

                y_labels (list[str] | None): Optional custom labels for the y-axis series.
                    If None, the `y_keys` are used as labels. Must match `y_keys` length.

                horizontal_lines (list[dict[str, Any]] | None): Optional reference lines drawn across
                    the chart. Each dictionary should contain:
                    - "value" (float, required): The y-axis value where the line is drawn
                    - "label" (str, optional): Text label for the line
                    - "color" (str, optional): HEX color code (e.g., "#000000")

                description (str | None): Optional subtitle/description shown below the title.

                height (int): Chart height in pixels. Defaults to 400.
                    Recommended range: 300-800 pixels.

                y_axis_domain_min (float | None): Optional minimum value for y-axis scale.
                    Forces chart to start at this value instead of auto-scaling.

                y_axis_domain_max (float | None): Optional maximum value for y-axis scale.
                    Forces chart to end at this value instead of auto-scaling.

            Returns:
                ChartWidget: A configured chart widget ready for display in the UI.
                The widget includes all styling, data, and interactive features.

            Common mistakes:
                - Including color information in data objects (not needed for line charts)
                - Mismatched y_labels and y_keys lengths
                - Non-numeric values in y_key fields
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
            if horizontal_lines is not None:
                parsed_horizontal_lines = parse_horizontal_lines(horizontal_lines)
            else:
                parsed_horizontal_lines = None

            return ChartWidget.create_line_chart(
                title=title,
                data=data,
                x_key=x_key,
                y_keys=y_keys,
                y_labels=y_labels,
                description=description,
                height=height,
                horizontal_lines=parsed_horizontal_lines,
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
            tool_answer_questionaire_question,
            tool_get_questionaire_answer,
            tool_store_memory,
            tool_create_bar_chart,
            tool_create_line_chart,
            tool_get_steps_data,
            tool_calculate_zlm_scores,
            tool_create_zlm_chart,
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
