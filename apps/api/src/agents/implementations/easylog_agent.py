import io
import json
import re
import uuid
from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

import httpx
from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from PIL import Image, ImageOps
from pydantic import BaseModel, Field
from src.agents.base_agent import BaseAgent
from src.agents.tools.base_tools import BaseTools
from src.agents.tools.easylog_backend_tools import EasylogBackendTools
from src.agents.tools.easylog_sql_tools import EasylogSqlTools
from src.models.chart_widget import ChartWidget
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
        default="anthropic/claude-3.7-sonnet:thinking",
        description="The model identifier to use for this role, e.g., 'openai/gpt-4.1' or any model from https://openrouter.ai/models.",
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


class EasyLogAgentConfig(BaseModel):
    roles: list[RoleConfig] = Field(
        default_factory=lambda: [
            RoleConfig(
                name="EasyLogAssistant",
                prompt="Je bent een vriendelijke assistent die helpt met het geven van demos van wat je allemaal kan",
                model="anthropic/claude-3.7-sonnet:thinking",
                tools_regex=".*",
                allowed_subjects=None,
                questionaire=[],
            )
        ]
    )
    prompt: str = Field(
        default="You can use the following roles: {available_roles}.\nYou are currently acting as the role: {current_role}.\nYour specific instructions for this role are: {current_role_prompt}.\nThis prompt may include details from a questionnaire. Use the provided tools to interact with the questionnaire if needed.\nThe current time is: {current_time}."
    )


class DefaultKeyDict(dict):
    def __missing__(self, key):
        return f"[missing:{key}]"


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


class EasyLogAgent(BaseAgent[EasyLogAgentConfig]):
    async def get_current_role(self) -> RoleConfig:
        role = await self.get_metadata("current_role", self.config.roles[0].name)
        if role not in [role.name for role in self.config.roles]:
            role = self.config.roles[0].name

        return next(
            role_config for role_config in self.config.roles if role_config.name == role
        )

    def get_tools(self) -> list[Callable]:
        # EasyLog-specific tools
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
        def tool_example_chart() -> ChartWidget:
            """Create a simple example bar chart with two bars.

            Returns:
                ChartWidget: A bar chart widget showing two example bars.
            """
            return ChartWidget.create_bar_chart(
                title="Example chart",
                data=[
                    {"name": "James", "value": 10},
                    {"name": "John", "value": 20},
                ],
                x_key="name",
                y_keys=["value"],
            )

        def tool_create_bar_chart(
            title: str,
            data: list[dict[str, Any]],
            x_key: str,
            y_keys: list[str],
            y_labels: list[str] | None = None,
            colors: list[str] | None = None,
            description: str | None = None,
            height: int = 400,
        ) -> ChartWidget:
            """Create a bar chart with customizable styles for each series.

            Args:
                title: Chart title.
                data: List of data objects for the chart.
                x_key: Key in data objects for the x-axis.
                y_keys: Keys in data objects for the y-axis values.
                y_labels: Optional labels for y-axis values (defaults to y_keys).
                description: Optional chart description.
                height: Chart height in pixels.
                colors: Optional list of colors for each bar series.

            Y labels and Y keys must be of same lenght.
            Colors must be of same lenght as y_keys.

            Example:
                title: "Sales by Product"
                data: [
                    {"product": "Product A", "sales": 100},
                    {"product": "Product B", "sales": 200},
                ]
                x_key: "product"
                y_keys: ["sales"]
                y_labels: ["Sales"]
                colors: ["#FF0000"]
                description: "Sales by Product"
                height: 400
            Returns:
                A ChartWidget object representing the bar chart.
            """
            if y_labels is not None and len(y_keys) != len(y_labels):
                raise ValueError("y_keys and y_labels must have the same length")

            return ChartWidget.create_bar_chart(
                title=title,
                data=data,
                x_key=x_key,
                y_keys=y_keys,
                y_labels=y_labels,
                description=description,
                height=height,
            )

        # Interaction tools
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

        # Assemble and return the complete tool list
        return [
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
            tool_example_chart,
            tool_create_bar_chart,
            # Interaction tools
            tool_ask_multiple_choice,
            # Image tools
            tool_download_image,
            # Schedule and reminder tools
            tool_set_recurring_task,
            tool_add_reminder,
            tool_remove_recurring_task,
            tool_remove_reminder,
            # System tools
            BaseTools.tool_noop,
        ]

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        # Get the current role
        role_config = await self.get_current_role()

        # Get the available tools
        tools = self.get_tools()

        # Filter tools based on the role's regex pattern
        tools = [
            tool
            for tool in tools
            if re.match(role_config.tools_regex, tool.__name__)
            or tool.__name__ == BaseTools.tool_noop.__name__
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
            formatted_current_role_prompt = role_config.prompt.format_map(
                DefaultKeyDict(questionnaire_format_kwargs)
            )
        except Exception as e:
            self.logger.warning(f"Error formatting role prompt: {e}")
            formatted_current_role_prompt = role_config.prompt

        # Gather reminders and recurring tasks
        recurring_tasks = await self.get_metadata("recurring_tasks", [])
        reminders = await self.get_metadata("reminders", [])

        # Prepare the main content for the LLM
        main_prompt_format_args = {
            "current_role": role_config.name,
            "current_role_prompt": formatted_current_role_prompt,
            "available_roles": "\\n".join(
                [f"- {role.name}: {role.prompt}" for role in self.config.roles]
            ),
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "recurring_tasks": "\\n".join(
                [
                    f"- {task['id']}: {task['cron_expression']} - {task['task']}"
                    for task in recurring_tasks
                ]
            ),
            "reminders": "\\n".join(
                [
                    f"- {reminder['id']}: {reminder['date']} - {reminder['message']}"
                    for reminder in reminders
                ]
            ),
        }
        main_prompt_format_args.update(questionnaire_format_kwargs)

        try:
            llm_content = self.config.prompt.format_map(
                DefaultKeyDict(main_prompt_format_args)
            )
        except Exception as e:
            self.logger.warning(f"Error formatting system prompt: {e}")
            # Fallback to a simple format
            llm_content = (
                f"Role: {role_config.name}\nPrompt: {formatted_current_role_prompt}"
            )

        # Create the completion request
        response = await self.client.chat.completions.create(
            model=role_config.model,
            messages=[
                {
                    "role": "developer",
                    "content": llm_content,
                },
                *messages,
            ],
            stream=True,
            tools=[function_to_openai_tool(tool) for tool in tools],
            tool_choice="auto",
        )

        return response, tools
