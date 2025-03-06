import inspect
import json
import logging
import os
from abc import abstractmethod
from collections.abc import AsyncGenerator, Callable, Coroutine, Generator
from types import UnionType
from typing import (
    Any,
    Generic,
    TypeVar,
    Union,
    get_args,
)

import pymysql
from prisma.models import processed_pdfs, threads
from pydantic import BaseModel

from src.lib.prisma import prisma
from src.logger import logger
from src.models.messages import Message, MessageContent, TextContent
from src.services.easylog_backend.backend_service import BackendService
from src.services.easylog_backend.easylog_sql_service import EasylogSqlService
from src.settings import settings

TConfig = TypeVar("TConfig", bound=BaseModel)


class BaseAgent(Generic[TConfig]):
    """Base class for all agents."""

    _thread: threads | None = None

    def __init__(self, thread_id: str, backend: BackendService, **kwargs: dict[str, Any]) -> None:
        self._thread_id = thread_id
        self._raw_config = kwargs
        self._thread = None

        self.easylog_backend = backend
        self.easylog_sql_service = EasylogSqlService(
            ssh_key_path=settings.EASYLOG_SSH_KEY_PATH,
            ssh_host=settings.EASYLOG_SSH_HOST,
            ssh_username=settings.EASYLOG_SSH_USERNAME,
            db_host=settings.EASYLOG_DB_HOST,
            db_port=settings.EASYLOG_DB_PORT,
            db_user=settings.EASYLOG_DB_USER,
            db_name=settings.EASYLOG_DB_NAME,
            db_password=settings.EASYLOG_DB_PASSWORD,
        )

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
    def easylog_db(self) -> pymysql.Connection:
        if not self.easylog_sql_service.db:
            raise ValueError("Easylog database connection not initialized")

        return self.easylog_sql_service.db

    @abstractmethod
    def on_message(self, messages: list[Message]) -> AsyncGenerator[TextContent, None]:
        raise NotImplementedError()

    @abstractmethod
    def get_tools(
        self,
    ) -> dict[str, Callable[[], Any] | Callable[[], Coroutine[Any, Any, Any]]]:
        raise NotImplementedError()

    def get_env(self, key: str) -> str:
        """A convenience method to get an environment variable."""

        env = os.getenv(key)

        if env is None:
            raise ValueError(f"Environment variable {key} is not found. Make sure .env file exists and {key} is set.")

        return env

    def forward(
        self,
        messages: list[Message],
    ) -> AsyncGenerator[MessageContent, None]:
        """
        Forward the messages to the agent. Returns a generator of message contents.

        Args:
            messages: The messages to forward to the agent.

        Returns:
            A generator of messages.
        """

        logger.info(f"Forwarding message to agent: {self.__class__.__name__}")

        generator = self.on_message(messages)

        if not inspect.isasyncgen(generator):
            if inspect.isgenerator(generator):
                logger.warning("on_message returned a sync generator, converting to async generator")
                generator = self._sync_to_async_generator(generator)
            else:
                raise ValueError("on_message must return either a sync or async generator")

        return generator

    def get_metadata(self, key: str, default: Any | None = None) -> Any:
        metadata: dict = json.loads((self._get_thread()).metadata or "{}")

        return metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        metadata: dict = json.loads((self._get_thread()).metadata or "{}")
        metadata[key] = value

        prisma.threads.update(where={"id": self._thread_id}, data={"metadata": json.dumps(metadata)})

    def get_knowledge(self) -> list[processed_pdfs]:
        return prisma.processed_pdfs.find_many(
            include={"object": True},
        )

    def _get_thread(self) -> threads:
        """Get the thread for the agent."""

        if self._thread is None:
            self._thread = prisma.threads.find_first_or_raise(where={"id": self._thread_id})

        return self._thread

    async def _sync_to_async_generator(self, sync_gen: Generator) -> AsyncGenerator:
        for item in sync_gen:
            yield item

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
