from collections.abc import Callable, Iterable

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel, Field
from src.agents.base_agent import BaseAgent
from src.agents.tools.knowledge_graph_tools import KnowledgeGraphTools
from src.utils.function_to_openai_tool import function_to_openai_tool


class RoleConfig(BaseModel):
    name: str
    prompt: str
    model: str


class MUMCAgentConfig(BaseModel):
    roles: list[RoleConfig] = Field(
        default_factory=lambda: [
            RoleConfig(
                name="Coach",
                prompt="You are a helpful friendly care taker for COPD patients.",
                model="openai/gpt-4.1",
            )
        ]
    )
    prompt: str = Field(
        default="You can use the following roles: {available_roles}. You are currently using the role: {current_role}. Your prompt is: {current_role_prompt}."
    )


class PersonEntity(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    birth_date: str | None = None
    gender: str | None = None


class MUMCAgent(BaseAgent[MUMCAgentConfig]):
    def get_tools(self) -> list[Callable]:
        knowledge_graph_tools = KnowledgeGraphTools(
            entities={"Person": PersonEntity},
            group_id=self.thread_id,
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

        return [
            *knowledge_graph_tools.all_tools,
            tool_set_current_role,
        ]

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        tools = self.get_tools()

        role = await self.get_metadata("current_role", self.config.roles[0].name)
        if role not in [role.name for role in self.config.roles]:
            role = self.config.roles[0].name

        role_config = next(
            role_config for role_config in self.config.roles if role_config.name == role
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
