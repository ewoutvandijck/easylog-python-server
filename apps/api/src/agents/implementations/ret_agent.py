import json
import os
from collections.abc import Callable, Iterable
from glob import glob

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

        return [
            tool_search_documents,
            tool_get_document_contents,
            tool_ask_multiple_choice,
            tool_load_excel_data,
            *easylog_sql_tools.all_tools,
            *easylog_backend_tools.all_tools,
            BaseTools.tool_noop,
        ]

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam]
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
