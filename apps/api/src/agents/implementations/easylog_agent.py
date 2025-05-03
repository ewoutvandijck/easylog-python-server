import io
import json
import re
import uuid
from collections.abc import Callable, Iterable
from datetime import datetime

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
from src.agents.tools.knowledge_graph_tools import KnowledgeGraphTools
from src.models.chart_widget import ChartWidget
from src.settings import settings
from src.utils.function_to_openai_tool import function_to_openai_tool
from apps.api.src.agents.implementations.debug_agent import RoleConfig, CarEntity, PersonEntity, JobEntity


class EasylogAgentConfig(BaseModel):
    roles: list[RoleConfig] = Field(
        default_factory=lambda: [
            RoleConfig(
                name="James",
                prompt="You are a helpful assistant.",
                model="openai/gpt-4.1",
                tools_regex=".*",
                allowed_subjects=None,
            )
        ]
    )
    prompt: str = Field(
        default="You can use the following roles: {available_roles}. You are currently using the role: {current_role}. Your prompt is: {current_role_prompt}. You can use the following recurring tasks: {recurring_tasks}. You can use the following reminders: {reminders}. The current time is: {current_time}."
    )


class EasylogAgent(BaseAgent[EasylogAgentConfig]):
    async def get_current_role(self) -> RoleConfig:
        role = await self.get_metadata("current_role", self.config.roles[0].name)
        if role not in [role.name for role in self.config.roles]:
            role = self.config.roles[0].name

        return next(role_config for role_config in self.config.roles if role_config.name == role)

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

        return [
            *easylog_backend_tools.all_tools,
            *easylog_sql_tools.all_tools,
            *knowledge_graph_tools.all_tools,
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
            if re.match(role_config.tools_regex, tool.__name__) or tool.__name__ == BaseTools.tool_noop.__name__
        ]

        recurring_tasks = await self.get_metadata("recurring_tasks", [])
        reminders = await self.get_metadata("reminders", [])

        response = await self.client.chat.completions.create(
            model=role_config.model,
            messages=[
                {
                    "role": "developer",
                    "content": self.config.prompt.format(
                        current_role=role_config.name,
                        current_role_prompt=role_config.prompt,
                        available_roles="\n".join([f"- {role.name}: {role.prompt}" for role in self.config.roles]),
                        recurring_tasks="\n".join(
                            [f"- {task['id']}: {task['cron_expression']} - {task['task']}" for task in recurring_tasks]
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