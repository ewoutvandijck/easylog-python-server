import json
import logging
from abc import abstractmethod
from collections.abc import AsyncGenerator, Iterable
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
from prisma import Json
from prisma.models import threads
from pydantic import BaseModel

from src.lib.prisma import prisma
from src.logger import logger

# from src.services.easylog_backend.easylog_sql_service import EasylogSqlService
from src.models.message_response import MessageAnnotation, MessageContent, MessageToolCall
from src.settings import settings

TConfig = TypeVar("TConfig", bound=BaseModel)


class BaseAgent(Generic[TConfig]):
    """Base class for all agents."""

    _thread: threads | None = None

    def __init__(self, thread_id: str, **kwargs: dict[str, Any]) -> None:
        self._thread_id = thread_id
        self._raw_config = kwargs

        # Initialize the client
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )

        # self.easylog_backend = backend
        # self.easylog_sql_service = EasylogSqlService(
        #     ssh_key_path=settings.EASYLOG_SSH_KEY_PATH,
        #     ssh_host=settings.EASYLOG_SSH_HOST,
        #     ssh_username=settings.EASYLOG_SSH_USERNAME,
        #     db_host=settings.EASYLOG_DB_HOST,
        #     db_port=settings.EASYLOG_DB_PORT,
        #     db_user=settings.EASYLOG_DB_USER,
        #     db_name=settings.EASYLOG_DB_NAME,
        #     db_password=settings.EASYLOG_DB_PASSWORD,
        # )

        logger.info(f"Initialized agent: {self.__class__.__name__}")
        logger.info(f"Using database: {settings.EASYLOG_DB_NAME}")

    def __init_subclass__(cls) -> None:
        cls._config_type = get_args(cls.__orig_bases__[0])[0]  # type: ignore
        logger.info(f"Initialized subclass: {cls.__name__}")

    @property
    def config(self) -> TConfig:
        return self._get_config(**self._raw_config)

    @property
    def logger(self) -> logging.Logger:
        return logger

    # @property
    # def easylog_db(self) -> pymysql.Connection:
    #     if not self.easylog_sql_service.db:
    #         raise ValueError("Easylog database connection not initialized")

    #     return self.easylog_sql_service.db

    @abstractmethod
    async def on_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> AsyncStream[ChatCompletionChunk] | ChatCompletion:
        raise NotImplementedError()

    async def forward_message(
        self, messages: Iterable[ChatCompletionMessageParam]
    ) -> AsyncGenerator[MessageToolCall | MessageAnnotation | MessageContent, None]:
        raise NotImplementedError("Forward message not implemented")

        yield MessageToolCall(
            id="1", message_id="1", name="test", arguments={"test": "test"}, result={"test": "test"}, is_error=False
        )

    def get_metadata(self, key: str, default: Any | None = None) -> Any:
        metadata: dict = json.loads((self._get_thread()).metadata or "{}")

        return metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        metadata: dict = json.loads((self._get_thread()).metadata or "{}")
        metadata[key] = value

        prisma.threads.update(where={"id": self._thread_id}, data={"metadata": Json(metadata)})

    def _get_thread(self) -> threads:
        """Get the thread for the agent."""

        if self._thread is None:
            self._thread = prisma.threads.find_first_or_raise(where={"id": self._thread_id})

        return self._thread

    def _get_config(self, **kwargs: dict[str, Any]) -> TConfig:
        """Parse kwargs into the config type specified by the child class"""
        # Get the generic parameters using typing.get_args
        # Get the actual config type from the class's generic parameters

        if not self._config_type:
            raise ValueError("Could not determine config type from class definition")

        # Handle Union types by trying each type until one works
        if (hasattr(self._config_type, "__origin__") and self._config_type.__origin__ is Union) or isinstance(
            self._config_type, UnionType
        ):
            for type_option in get_args(self._config_type):
                try:
                    return type_option(**kwargs)
                except (ValueError, TypeError):
                    continue
            raise ValueError(f"None of the union types {self._config_type} could parse the config")

        # Handle single type
        return self._config_type(**kwargs)
