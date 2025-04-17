import json
from collections.abc import Callable, Iterable

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel

from src.agents.base_agent import BaseAgent
from src.agents.tools.easylog_backend_tools import EasylogBackendTools
from src.agents.tools.easylog_sql_tools import EasylogSqlTools
from src.agents.tools.knowledge_graph_tools import KnowledgeGraphTools
from src.settings import settings
from src.utils.function_to_openai_tool import function_to_openai_tool


class DebugAgentConfig(BaseModel):
    pass


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


class DebugAgent(BaseAgent[DebugAgentConfig]):
    async def on_init(self) -> None:
        self.easylog_backend_tools = EasylogBackendTools(
            bearer_token=self.request_headers.get("X-Easylog-Bearer-Token", ""),
            base_url=self.request_headers.get("X-Easylog-Base-Url", "https://staging.easylog.nu/api/v2"),
        )

        self.easylog_sql_tools = EasylogSqlTools(
            ssh_key_path=settings.EASYLOG_SSH_KEY_PATH,
            ssh_host=settings.EASYLOG_SSH_HOST,
            ssh_username=settings.EASYLOG_SSH_USERNAME,
            db_password=settings.EASYLOG_DB_PASSWORD,
            db_user=settings.EASYLOG_DB_USER,
            db_host=settings.EASYLOG_DB_HOST,
            db_port=settings.EASYLOG_DB_PORT,
            db_name=settings.EASYLOG_DB_NAME,
        )

        self.knowledge_graph_tools = KnowledgeGraphTools(
            thread_id=self.thread_id,
            entities={"Car": CarEntity, "Person": PersonEntity, "Job": JobEntity},
        )

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        def test(name: str) -> str:
            return f"Hello, {name}!"

        self.logger.info(f"Messages: {json.dumps(messages, indent=2)}")

        response = await self.client.chat.completions.create(
            model="openai/gpt-4.1",
            messages=messages,
            stream=True,
            tools=[
                *[function_to_openai_tool(tool) for tool in self.easylog_backend_tools.all_tools],
                *[function_to_openai_tool(tool) for tool in self.easylog_sql_tools.all_tools],
                *[function_to_openai_tool(tool) for tool in self.knowledge_graph_tools.all_tools],
            ],
            tool_choice="auto",
        )

        return response, [test]
