import json
import re
import uuid
from collections.abc import Callable, Iterable
from datetime import datetime

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from src.agents.base_agent import BaseAgent
from src.agents.tools.base_tools import BaseTools
from src.models.multiple_choice_widget import Choice, MultipleChoiceWidget
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
    name: str = Field(default="James")
    prompt: str = Field(default="You are a helpful assistant.")
    model: str = Field(default="openai/gpt-4.1")
    tools_regex: str = Field(default=".*")
    allowed_subjects: list[str] | None = Field(default=None)
    questionaire: list[QuestionaireQuestionConfig] = Field(
        default_factory=list,
        description="A list of questions (as QuestionaireQuestionConfig) that this role should ask the user, enabling dynamic, role-specific data collection.",
    )


class MUMCAgentConfig(BaseModel):
    roles: list[RoleConfig] = Field(
        default_factory=lambda: [
            RoleConfig(
                name="Coach",
                prompt="You are a helpful friendly supporting care taker for COPD patients.",
                model="openai/gpt-4.1",
                tools_regex=".*",
                allowed_subjects=None,
                questionaire=[],  # Added empty list for questionaire
            )
        ]
    )
    prompt: str = Field(
        default="You can use the following roles: {available_roles}.\\nYou are currently acting as the role: {current_role}.\\nYour specific instructions for this role are: {current_role_prompt}.\\nYou can use the following recurring tasks: {recurring_tasks}.\\nYou can use the following reminders: {reminders}.\\nThe current time is: {current_time}."
    )


class DefaultKeyDict(dict):
    def __missing__(self, key):
        return f"[missing:{key}]"


class MUMCAgent(BaseAgent[MUMCAgentConfig]):
    async def get_current_role(self) -> RoleConfig:
        role = await self.get_metadata("current_role", self.config.roles[0].name)
        if role not in [role.name for role in self.config.roles]:
            role = self.config.roles[0].name

        return next(
            role_config for role_config in self.config.roles if role_config.name == role
        )

    def get_tools(self) -> list[Callable]:
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

        async def tool_remove_recurring_task(task_id: str) -> str:
            """Remove a recurring task.

            Args:
                task_id (str): The ID of the task to remove.
            """
            existing_tasks: list[dict[str, str]] = await self.get_metadata(
                "recurring_tasks", []
            )

            existing_tasks = [task for task in existing_tasks if task["id"] != task_id]

            await self.set_metadata("recurring_tasks", existing_tasks)

            return f"Recurring task {task_id} removed"

        async def tool_remove_reminder(task_id: str) -> str:
            """Remove a reminder.

            Args:
                id (str): The ID of the reminder to remove.
            """
            existing_reminders: list[dict[str, str]] = await self.get_metadata(
                "reminders", []
            )

            existing_reminders = [
                reminder for reminder in existing_reminders if reminder["id"] != task_id
            ]

            await self.set_metadata("reminders", existing_reminders)

            return f"Reminder {task_id} removed"

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

        return [
            tool_search_documents,
            tool_get_document_contents,
            # *knowledge_graph_tools.all_tools,
            tool_set_current_role,
            tool_set_recurring_task,
            tool_remove_recurring_task,
            tool_add_reminder,
            tool_remove_reminder,
            tool_ask_multiple_choice,
            tool_get_questionaire_answer,
            tool_answer_questionaire_question,
            BaseTools.tool_noop,
        ]

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        role_config = await self.get_current_role()

        tools = self.get_tools()

        tools = [
            tool
            for tool in tools
            if re.match(role_config.tools_regex, tool.__name__)
            or tool.__name__ == BaseTools.tool_noop.__name__
        ]

        recurring_tasks = await self.get_metadata("recurring_tasks", [])
        reminders = await self.get_metadata("reminders", [])

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

        formatted_current_role_prompt = role_config.prompt.format_map(
            DefaultKeyDict(questionnaire_format_kwargs)
        )

        # Prepare the main content for the LLM
        main_prompt_format_args = {
            "current_role": role_config.name,
            "current_role_prompt": formatted_current_role_prompt,
            "available_roles": "\\n".join(
                [f"- {role.name}: {role.prompt}" for role in self.config.roles]
            ),
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
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        main_prompt_format_args.update(questionnaire_format_kwargs)

        llm_content = self.config.prompt.format_map(
            DefaultKeyDict(main_prompt_format_args)
        )

        response = await self.client.chat.completions.create(
            model=role_config.model,
            messages=[
                {
                    "role": "developer",
                    "content": llm_content, # Use the prepared llm_content
                },
                *messages,
            ],
            stream=True,
            tools=[function_to_openai_tool(tool) for tool in tools],
            tool_choice="auto",
        )

        return response, tools
