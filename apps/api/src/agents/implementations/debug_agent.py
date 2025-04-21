from collections.abc import Callable, Iterable

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from src.agents.base_agent import BaseAgent
from src.agents.tools.easylog_backend_tools import EasylogBackendTools
from src.agents.tools.easylog_sql_tools import EasylogSqlTools
from src.models.chart_widget import ChartWidget
from src.settings import settings
from src.utils.function_to_openai_tool import function_to_openai_tool


class RoleConfig(BaseModel):
    name: str
    prompt: str
    model: str


class DebugAgentConfig(BaseModel):
    roles: list[RoleConfig] = Field(
        default_factory=lambda: [
            RoleConfig(
                name="James",
                prompt="You are a helpful assistant.",
                model="openai/gpt-4.1",
            )
        ]
    )
    prompt: str = Field(
        default="You can use the following roles: {available_roles}. You are currently using the role: {current_role}. Your prompt is: {current_role_prompt}."
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


class DebugAgent(BaseAgent[DebugAgentConfig]):
    def get_tools(self) -> list[Callable]:
        easylog_backend_tools = EasylogBackendTools(
            bearer_token=self.request_headers.get("X-Easylog-Bearer-Token", ""),
            base_url=self.request_headers.get(
                "X-Easylog-Base-Url", "https://staging.easylog.nu/api/v2"
            ),
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

        # knowledge_graph_tools = KnowledgeGraphTools(
        #     thread_id=self.thread_id,
        #     entities={"Car": CarEntity, "Person": PersonEntity, "Job": JobEntity},
        # )

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

        def tool_example_chart() -> ChartWidget:
            return ChartWidget.create_bar_chart(
                title="Example chart",
                data=[
                    {"name": "James", "value": 10},
                    {"name": "John", "value": 20},
                ],
                x_key="name",
                y_keys=["value"],
            )

        return [
            *easylog_backend_tools.all_tools,
            *easylog_sql_tools.all_tools,
            # *knowledge_graph_tools.all_tools,
            tool_set_current_role,
            tool_example_chart,
        ]

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        tools = self.get_tools()

        self.logger.info(messages)

        role = await self.get_metadata("current_role", self.config.roles[0].name)
        if role not in [role.name for role in self.config.roles]:
            role = self.config.roles[0].name

        role_config = next(
            role_config for role_config in self.config.roles if role_config.name == role
        )

        self.logger.info(
            self.config.prompt.format(
                current_role=role,
                current_role_prompt=role_config.prompt,
                available_roles="\n".join(
                    [f"'{role.name}'" for role in self.config.roles]
                ),
            )
        )

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
                    ),
                },
                *messages,
            ],
            stream=True,
            tools=[function_to_openai_tool(tool) for tool in tools],
            tool_choice="auto",
        )

        return response, tools
