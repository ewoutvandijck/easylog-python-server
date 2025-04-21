import asyncio
import json
import logging
import uuid
from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable, Iterable
from types import UnionType
from typing import (
    Any,
    Generic,
    TypeVar,
    Union,
    get_args,
)

from openai import AsyncOpenAI, AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from PIL import Image
from prisma import Json
from prisma.models import threads
from pydantic import BaseModel

from src.lib.prisma import prisma
from src.logger import logger
from src.models.chart_widget import ChartWidget
from src.models.messages import MessageContent, TextContent, TextDeltaContent, ToolResultContent, ToolUseContent
from src.models.stream_tool_call import StreamToolCall
from src.settings import settings
from src.utils.image_to_base64 import image_to_base64

TConfig = TypeVar("TConfig", bound=BaseModel)


class BaseAgent(Generic[TConfig]):
    """Base class for all agents."""

    _thread: threads | None = None

    def __init__(self, thread_id: str, request_headers: dict, **kwargs: dict[str, Any]) -> None:
        self._raw_config = kwargs
        self.thread_id = thread_id
        self.request_headers = request_headers

        # Initialize the client
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )

        self.on_init()

        logger.info(f"Initialized agent: {self.__class__.__name__}")

    def __init_subclass__(cls) -> None:
        cls._config_type = get_args(cls.__orig_bases__[0])[0]  # type: ignore
        logger.info(f"Initialized subclass: {cls.__name__}")

    @property
    def config(self) -> TConfig:
        return self._get_config(**self._raw_config)

    @property
    def logger(self) -> logging.Logger:
        return logger

    @abstractmethod
    async def on_message(
        self,
        messages: Iterable[ChatCompletionMessageParam],
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        raise NotImplementedError()

    @abstractmethod
    def on_init(self) -> None:
        pass

    async def forward_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> AsyncGenerator[MessageContent, None]:
        result, tools = await self.on_message(messages)

        async for chunk in (
            self._handle_stream(result, tools)
            if isinstance(result, AsyncStream)
            else self._handle_completion(result, tools)
        ):
            yield chunk

    async def get_metadata(self, key: str, default: Any | None = None) -> Any:
        metadata: dict = dict((await self._get_thread()).metadata) or {}

        return metadata.get(key, default)

    async def set_metadata(self, key: str, value: Any) -> None:
        metadata: dict = dict((await self._get_thread()).metadata) or {}
        metadata[key] = value

        await prisma.threads.update(where={"id": self.thread_id}, data={"metadata": Json(metadata)})

    async def _get_thread(self) -> threads:
        """Get the thread for the agent."""

        if self._thread is None:
            self._thread = await prisma.threads.find_first_or_raise(where={"id": self.thread_id})

        return self._thread

    def _get_config(self, **kwargs: dict[str, Any]) -> TConfig:
        """Parse kwargs into the config type specified by the child class"""

        if not self._config_type:
            raise ValueError("Could not determine config type from class definition")

        if (hasattr(self._config_type, "__origin__") and self._config_type.__origin__ is Union) or isinstance(
            self._config_type, UnionType
        ):
            for type_option in get_args(self._config_type):
                try:
                    return type_option(**kwargs)
                except (ValueError, TypeError):
                    continue

            raise ValueError(f"None of the union types {self._config_type} could parse the config")

        return self._config_type(**kwargs)

    async def _handle_tool_call(
        self, name: str, tool_call_id: str, arguments: dict[str, Any], tools: list[Callable]
    ) -> ToolResultContent:
        try:
            tool = next(tool for tool in tools if tool.__name__ == name)
        except StopIteration as e:
            raise ValueError(f"Tool {name} not found") from e

        try:
            result = await tool(**arguments) if asyncio.iscoroutinefunction(tool) else tool(**arguments)

            if isinstance(result, Image.Image):
                return ToolResultContent(
                    id=str(uuid.uuid4()),
                    tool_use_id=tool_call_id,
                    output=image_to_base64(result),
                    widget_type="image",
                    is_error=False,
                )
            elif isinstance(result, ChartWidget):
                return ToolResultContent(
                    id=str(uuid.uuid4()),
                    tool_use_id=tool_call_id,
                    output=result.model_dump_json(),
                    widget_type="chart",
                    is_error=False,
                )
            else:
                return ToolResultContent(
                    id=str(uuid.uuid4()),
                    tool_use_id=tool_call_id,
                    output=str(result),
                    is_error=False,
                )
        except Exception as e:
            return ToolResultContent(
                id=str(uuid.uuid4()),
                tool_use_id=tool_call_id,
                output=f"Error: {e}",
                is_error=True,
            )

    async def _handle_stream(
        self, stream: AsyncStream[ChatCompletionChunk], tools: list[Callable]
    ) -> AsyncGenerator[MessageContent, None]:
        final_tool_calls: dict[int, StreamToolCall] = {}

        text_content: str | None = ""
        text_id = str(uuid.uuid4())
        try:
            async for event in stream:
                if event.choices[0].delta.content is not None:
                    text_content = (
                        event.choices[0].delta.content
                        if text_content is None
                        else text_content + event.choices[0].delta.content
                    )

                    yield TextDeltaContent(
                        id=text_id,
                        delta=event.choices[0].delta.content,
                    )

                for tool_call in event.choices[0].delta.tool_calls or []:
                    index = tool_call.index

                    if tool_call.function is None or tool_call.function.arguments is None:
                        self.logger.warning(f"Skipping tool call {tool_call} because it is invalid")
                        continue

                    if (
                        index not in final_tool_calls
                        and tool_call.function.name is not None
                        and tool_call.id is not None
                    ):
                        final_tool_calls[index] = StreamToolCall(
                            tool_call_id=tool_call.id,
                            name=tool_call.function.name,
                            arguments=tool_call.function.arguments,
                        )
                    else:
                        final_tool_calls[index].arguments += tool_call.function.arguments

            if text_content is not None:
                yield TextContent(
                    id=text_id,
                    text=text_content,
                )

            for _, tool_call in final_tool_calls.items():
                input_data = json.loads(tool_call.arguments)

                yield ToolUseContent(
                    id=str(uuid.uuid4()),
                    tool_use_id=tool_call.tool_call_id,
                    name=tool_call.name,
                    input=input_data,
                )

                yield await self._handle_tool_call(tool_call.name, tool_call.tool_call_id, input_data, tools)
        except Exception as e:
            self.logger.error(f"Error handling tool call: {e}")
            raise e

    async def _handle_completion(
        self, completion: ChatCompletion, tools: list[Callable]
    ) -> AsyncGenerator[MessageContent, None]:
        if len(completion.choices or []) == 0:
            raise ValueError(
                "No choices found in completion, this usually means the messages weren't forwarded correctly"
            )

        choice = completion.choices[0]

        if choice.message.content is not None:
            yield TextContent(
                id=str(uuid.uuid4()),
                text=choice.message.content,
            )

        for tool_call in choice.message.tool_calls or []:
            input_data = json.loads(tool_call.function.arguments)

            yield ToolUseContent(
                id=str(uuid.uuid4()),
                tool_use_id=tool_call.id,
                name=tool_call.function.name,
                input=input_data,
            )

            yield await self._handle_tool_call(tool_call.function.name, tool_call.id, input_data, tools)
