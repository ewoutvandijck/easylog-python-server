from typing import AsyncGenerator

from pydantic import BaseModel


def create_sse_event(event: str, data: str) -> str:
    return f"event: {event}\ndata: {data}\n\n"


async def pydantic_to_sse_stream(
    event_name: str, generator: AsyncGenerator[BaseModel, None]
) -> AsyncGenerator[str, None]:
    """Convert a generator of Pydantic models to an SSE stream.

    Args:
        event_name (str): The event name.
        generator (AsyncGenerator[BaseModel, None]): The generator of Pydantic models.

    Returns:
        AsyncGenerator[str, None]: A generator of SSE events.

    Yields:
        Iterator[AsyncGenerator[str, None]]: A generator of SSE events.
    """

    async for chunk in generator:
        yield create_sse_event(event_name, chunk.model_dump_json())
