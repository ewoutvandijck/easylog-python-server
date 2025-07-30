import asyncio
import io
import json
import logging
import uuid
from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable, Iterable, Sequence
from types import UnionType
from typing import (
    Any,
    Generic,
    TypeVar,
    Union,
    get_args,
)

from openai import AsyncStream
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from PIL import Image
from prisma import Json
from prisma.models import documents, threads
from pydantic import BaseModel, Field
from weaviate.classes.query import Filter, MetadataQuery
from weaviate.collections.classes.types import Properties
from weaviate.collections.collection import CollectionAsync

from src.agents.tools.base_tools import BaseTools
from src.lib.openai import openai_client
from src.lib.prisma import prisma
from src.lib.supabase import create_supabase
from src.lib.weaviate import weaviate_client
from src.logger import logger
from src.models.chart_widget import ChartWidget
from src.models.image_widget import ImageWidget
from src.models.messages import MessageContent, TextContent, TextDeltaContent, ToolResultContent, ToolUseContent
from src.models.multiple_choice_widget import MultipleChoiceWidget
from src.models.stream_tool_call import StreamToolCall
from src.services.one_signal.one_signal_service import OneSignalService
from src.utils.image_to_base64 import image_to_base64
from src.settings import settings

TConfig = TypeVar("TConfig", bound=BaseModel)


class SuperAgentConfig(BaseModel, Generic[TConfig]):
    agent_config: TConfig
    cron_expression: str = Field(default="* * * * *")
    headers: dict = Field(default_factory=dict)


class BaseAgent(Generic[TConfig]):
    """Base class for all agents."""

    _thread: threads | None = None
    _metadata: dict | None = None
    _onesignal_api_key: str | None = None

    def __init__(self, thread_id: str, request_headers: dict, **kwargs: dict[str, Any]) -> None:
        self._raw_config = kwargs
        self.thread_id = thread_id
        self.request_headers = request_headers

        # Initialize the client
        self.client = openai_client

        self.on_init()

        self.one_signal = OneSignalService(settings.ONESIGNAL_APPERTO_API_KEY)

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

    @property
    def documents_collection(self) -> CollectionAsync[Properties, None]:
        return weaviate_client.collections.get("documents")

    @abstractmethod
    async def on_message(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        retry_count: int = 0,
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]]:
        raise NotImplementedError()

    @abstractmethod
    async def on_super_agent_call(
        self,
        messages: Iterable[ChatCompletionMessageParam],
    ) -> tuple[AsyncStream[ChatCompletionChunk] | ChatCompletion, list[Callable]] | None:
        raise NotImplementedError()

    @abstractmethod
    def on_init(self) -> None:
        pass

    def _set_onesignal_api_key(self, api_key: str) -> None:
        self._onesignal_api_key = api_key

    @staticmethod
    def super_agent_config() -> SuperAgentConfig[TConfig] | None:
        return None

    async def forward_message(
        self, messages: Iterable[ChatCompletionMessageParam], retry_count: int = 0
    ) -> AsyncGenerator[tuple[MessageContent, bool], None]:
        result, tools = await self.on_message(messages, retry_count)

        async for chunk, should_stop in (
            self._handle_stream(result, tools, messages, retry_count)
            if isinstance(result, AsyncStream)
            else self._handle_completion(result, tools, messages, retry_count)
        ):
            yield chunk, should_stop

    async def run_super_agent(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> AsyncGenerator[tuple[MessageContent, bool], None]:
        self.logger.info(f"Running super agent for {self.thread_id}")

        result = await self.on_super_agent_call(messages)

        if result is None:
            return

        result, tools = result

        async for chunk, should_stop in (
            self._handle_stream(result, tools, messages)
            if isinstance(result, AsyncStream)
            else self._handle_completion(result, tools, messages)
        ):
            yield chunk, should_stop

    async def get_metadata(self, key: str, default: Any | None = None) -> Any:
        if self._metadata is None:
            self._metadata = dict((await self._get_thread()).metadata) or {}

        return self._metadata.get(key, default)

    async def set_metadata(self, key: str, value: Any) -> None:
        if self._metadata is None:
            self._metadata = dict((await self._get_thread()).metadata) or {}

        self._metadata[key] = value

        await prisma.threads.update(where={"id": self.thread_id}, data={"metadata": Json(self._metadata)})

    async def get_document(self, document_path: str) -> dict:
        document = await prisma.documents.find_first_or_raise(where={"path": document_path})

        return dict(document.content)

    async def search_documents(
        self, search_query: str, subjects: Sequence[str] | None = None, limit: int = 5
    ) -> list[documents]:
        search_results = await self.documents_collection.query.hybrid(
            query=search_query,
            limit=limit,
            alpha=0.5,
            auto_limit=1,
            return_metadata=MetadataQuery.full(),
            filters=Filter.by_property("subject").contains_any(subjects) if subjects else None,
        )

        filenames = [
            filename
            for filename in (
                result.properties.get("file_name", "")
                for result in search_results.objects
                if result.metadata and result.metadata.score and result.metadata.score > 0
            )
            if isinstance(filename, str)
        ]

        if not filenames:
            return []

        return await prisma.documents.find_many(where={"file_name": {"in": filenames}})

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
    ) -> tuple[ToolResultContent, bool]:
        try:
            tool = next(tool for tool in tools if tool.__name__ == name)
        except StopIteration as e:
            raise ValueError(f"Tool {name} not found") from e

        try:
            tool_call_result = await tool(**arguments) if asyncio.iscoroutinefunction(tool) else tool(**arguments)

            logger.debug(f"Tool call result: {tool_call_result}")

            if (
                isinstance(tool_call_result, tuple)
                and len(tool_call_result) == 2
                and isinstance(tool_call_result[1], bool)
            ):
                result = tool_call_result[0]
                should_stop = tool_call_result[1]
            else:
                result = tool_call_result
                should_stop = False

            if should_stop:
                self.logger.debug(f"Tool {name} returned should_stop=True, cancelling agent call")

            if isinstance(result, ImageWidget) and result.mode == "image_url" or isinstance(result, Image.Image):
                supabase = await create_supabase()

                image = result if isinstance(result, Image.Image) else Image.open(io.BytesIO(result.data))

                if image.mode in ("RGBA", "LA", "P"):
                    image = image.convert("RGB")

                contents = io.BytesIO()
                image.save(contents, format="JPEG")

                result = await supabase.storage.from_("user-uploads").upload(
                    f"{self.thread_id}/{str(uuid.uuid4())}.jpg",
                    contents.getvalue(),
                    file_options={"content-type": "image/jpeg"},
                )

                url = await supabase.storage.from_("user-uploads").get_public_url(result.path)

                return (
                    ToolResultContent(
                        id=str(uuid.uuid4()),
                        tool_use_id=tool_call_id,
                        output=url,
                        widget_type="image_url",
                        is_error=False,
                    ),
                    should_stop,
                )
            elif isinstance(result, ImageWidget) and result.mode == "image":
                return (
                    ToolResultContent(
                        id=str(uuid.uuid4()),
                        tool_use_id=tool_call_id,
                        output=image_to_base64(Image.open(io.BytesIO(result.data))),
                        widget_type="image",
                        is_error=False,
                    ),
                    should_stop,
                )
            elif isinstance(result, ChartWidget):
                return (
                    ToolResultContent(
                        id=str(uuid.uuid4()),
                        tool_use_id=tool_call_id,
                        output=result.model_dump_json(),
                        widget_type="chart",
                        is_error=False,
                    ),
                    should_stop,
                )
            elif isinstance(result, MultipleChoiceWidget):
                return (
                    ToolResultContent(
                        id=str(uuid.uuid4()),
                        tool_use_id=tool_call_id,
                        output=result.model_dump_json(),
                        widget_type="multiple_choice",
                        is_error=False,
                    ),
                    should_stop,
                )
            elif isinstance(result, str):
                return (
                    ToolResultContent(
                        id=str(uuid.uuid4()),
                        tool_use_id=tool_call_id,
                        output=result,
                        widget_type="text",
                        is_error=False,
                    ),
                    should_stop,
                )
            else:
                return (
                    ToolResultContent(
                        id=str(uuid.uuid4()),
                        tool_use_id=tool_call_id,
                        output=str(result),
                        is_error=False,
                    ),
                    should_stop,
                )
        except Exception as e:
            return (
                ToolResultContent(
                    id=str(uuid.uuid4()),
                    tool_use_id=tool_call_id,
                    output=f"Error: {e}",
                    is_error=True,
                ),
                False,
            )

    async def _handle_stream(
        self,
        stream: AsyncStream[ChatCompletionChunk],
        tools: list[Callable],
        messages: Iterable[ChatCompletionMessageParam],
        retry_count: int = 0,
    ) -> AsyncGenerator[tuple[MessageContent, bool], None]:
        final_tool_calls: dict[int, StreamToolCall] = {}
        text_content: str | None = None
        text_id = str(uuid.uuid4())

        try:
            async for event in stream:
                if event.choices[0].delta.content is not None:
                    text_content = (
                        event.choices[0].delta.content
                        if text_content is None
                        else text_content + event.choices[0].delta.content
                    )

                    yield (
                        TextDeltaContent(
                            id=text_id,
                            delta=event.choices[0].delta.content,
                        ),
                        False,
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
                yield (
                    TextContent(
                        id=text_id,
                        text=text_content,
                    ),
                    False,
                )

            for _, tool_call in final_tool_calls.items():
                if tool_call.name == BaseTools.tool_call_super_agent.__name__:
                    async for chunk, should_stop in self.run_super_agent(messages):
                        yield chunk, should_stop

                    continue

                input_data = json.loads(tool_call.arguments or "{}")

                yield (
                    ToolUseContent(
                        id=str(uuid.uuid4()),
                        tool_use_id=tool_call.tool_call_id,
                        name=tool_call.name,
                        input=input_data,
                    ),
                    False,
                )

                yield await self._handle_tool_call(tool_call.name, tool_call.tool_call_id, input_data, tools)

            did_produce_content = len(final_tool_calls.items()) > 0 or (text_content and text_content.strip() != "")

            if not did_produce_content and retry_count < 3:
                self.logger.warning(f"No content produced, retrying {retry_count + 1} times")

                async for chunk in self.forward_message(messages, retry_count + 1):
                    yield chunk
            elif not did_produce_content:
                raise ValueError("The agent did not produce any content after 3 retries.")
        except Exception as e:
            self.logger.error(f"Error in _handle_stream: {e}")
            raise e

    async def _handle_completion(
        self,
        completion: ChatCompletion,
        tools: list[Callable],
        messages: Iterable[ChatCompletionMessageParam],
        retry_count: int = 0,
    ) -> AsyncGenerator[tuple[MessageContent, bool], None]:
        if len(completion.choices or []) == 0:
            raise ValueError(
                "No choices found in completion, this usually means the messages weren't forwarded correctly"
            )

        choice = completion.choices[0]

        if choice.message.content is not None:
            yield (
                TextContent(
                    id=str(uuid.uuid4()),
                    text=choice.message.content,
                ),
                False,
            )

        for tool_call in choice.message.tool_calls or []:
            if tool_call.function.name == BaseTools.tool_call_super_agent.__name__:
                async for chunk in self.run_super_agent(messages):
                    yield chunk

                continue

            input_data = json.loads(tool_call.function.arguments or "{}")

            yield (
                ToolUseContent(
                    id=str(uuid.uuid4()),
                    tool_use_id=tool_call.id,
                    name=tool_call.function.name,
                    input=input_data,
                ),
                False,
            )

            yield await self._handle_tool_call(tool_call.function.name, tool_call.id, input_data, tools)

        did_produce_content = len(choice.message.tool_calls or []) > 0 or (
            choice.message.content and choice.message.content.strip() != ""
        )

        if not did_produce_content and retry_count < 3:
            self.logger.warning(f"No content produced, retrying {retry_count + 1} times")

            async for chunk, should_stop in self.forward_message(messages, retry_count + 1):
                yield chunk, should_stop
        elif not did_produce_content:
            raise ValueError("The agent did not produce any content after 3 retries.")
