import io
from collections.abc import Callable, Iterable
from datetime import date

import httpx
from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from PIL import Image, ImageOps
from pydantic import BaseModel, Field

from src.agents.base_agent import BaseAgent
from src.agents.tools.easylog_backend_tools import EasylogBackendTools
from src.agents.tools.easylog_sql_tools import EasylogSqlTools
from src.agents.tools.knowledge_graph_tools import KnowledgeGraphTools
from src.models.chart_widget import ChartWidget
from src.settings import settings
from src.utils.function_to_openai_tool import function_to_openai_tool


class RoleConfig(BaseModel):
    name: str
    prompt: str
    model: str


class EasyLogAgentConfig(BaseModel):
    roles: list[RoleConfig] = Field(
        default_factory=lambda: [
            RoleConfig(
                name="EasyLogAssistant",
                prompt="Je bent een vriendelijke assistent die helpt met het geven van demos van wat je allemaal kan",
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


class EasyLogAgent(BaseAgent[EasyLogAgentConfig]):
    def get_tools(self) -> list[Callable]:
        # Get header in lowercase, given that its now a DICT and thus has been converted to lowercase
        easylog_backend_tools = EasylogBackendTools(
            bearer_token=self.request_headers.get("x-easylog-bearer-token", ""),
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

        knowledge_graph_tools = KnowledgeGraphTools(
            entities={"Car": CarEntity, "Person": PersonEntity, "Job": JobEntity},
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
                    self.logger.info(f"Resizing image from {image.width}x{image.height} to {new_size[0]}x{new_size[1]}")
                    image = image.resize(new_size, Image.Resampling.LANCZOS)

                return image

            except httpx.HTTPStatusError:
                raise
            except Image.UnidentifiedImageError:
                raise
            except Exception:
                raise

        def tool_get_current_date() -> str:
            """Return the current date.

            Returns:
                str: The current date in YYYY-MM-DD format.
            """
            return date.today().isoformat()

        return [
            *easylog_backend_tools.all_tools,
            *easylog_sql_tools.all_tools,
            *knowledge_graph_tools.all_tools,
            tool_set_current_role,
            tool_example_chart,
            tool_download_image,
            tool_get_current_date,
        ]

    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        tools = self.get_tools()

        role = await self.get_metadata("current_role", self.config.roles[0].name)
        if role not in [role.name for role in self.config.roles]:
            role = self.config.roles[0].name

        role_config = next(role_config for role_config in self.config.roles if role_config.name == role)

        current_date = date.today().isoformat()
        system_prompt = self.config.prompt.format(
            current_role=role,
            current_role_prompt=role_config.prompt,
            available_roles="\n".join([f"- {role.name}: {role.prompt}" for role in self.config.roles]),
        )
        system_prompt_with_date = f"{system_prompt}\n\nCurrent date is {current_date}."

        response = await self.client.chat.completions.create(
            model=role_config.model,
            messages=[
                {
                    "role": "developer",
                    "content": system_prompt_with_date,
                },
                *messages,
            ],
            stream=True,
            tools=[function_to_openai_tool(tool) for tool in tools],
            tool_choice="auto",
        )

        return response, tools
