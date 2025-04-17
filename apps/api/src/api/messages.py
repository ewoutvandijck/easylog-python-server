import json
from collections.abc import AsyncGenerator
from typing import Literal

from fastapi import APIRouter, HTTPException, Path, Query, Request, Response
from fastapi.responses import StreamingResponse

from src.lib.prisma import prisma
from src.logger import logger
from src.models.message_create import MessageCreateInput
from src.models.messages import Message
from src.models.pagination import Pagination
from src.services.messages.message_service import MessageService
from src.services.messages.utils.db_message_to_message_model import db_message_to_message_model
from src.utils.is_valid_uuid import is_valid_uuid
from src.utils.sse import create_sse_event

router = APIRouter()


@router.get(
    "/threads/{thread_id}/messages",
    name="get_messages",
    tags=["messages"],
    response_model=Pagination[Message],
    description="Retrieves all messages for a given thread. Returns a list of all messages by default in descending chronological order (newest first).",
)
async def get_messages(
    thread_id: str = Path(
        ...,
        description="The unique identifier of the thread. Can be either the internal ID or external ID.",
    ),
    limit: int = Query(default=10, ge=1),
    offset: int = Query(default=0, ge=0),
    order: Literal["asc", "desc"] = Query(default="asc"),
) -> Pagination[Message]:
    messages = await prisma.messages.find_many(
        where={"thread_id": thread_id} if is_valid_uuid(thread_id) else {"thread": {"is": {"external_id": thread_id}}},
        order=[{"created_at": order}],
        include={"contents": True},
        take=limit,
        skip=offset,
    )

    message_data = [db_message_to_message_model(message) for message in messages]

    return Pagination(data=message_data, limit=limit, offset=offset)


@router.post(
    "/threads/{thread_id}/messages",
    name="create_message",
    tags=["messages"],
    response_description="A stream of JSON-encoded message chunks",
    description="Creates a new message in the given thread. Will interact with the agent and return a stream of message chunks.",
)
async def create_message(
    message: MessageCreateInput,
    request: Request,
    thread_id: str = Path(
        ...,
        description="The unique identifier of the thread. Can be either the internal ID or external ID.",
    ),
) -> StreamingResponse:
    thread = await prisma.threads.find_first(
        where={"id": thread_id} if is_valid_uuid(thread_id) else {"external_id": thread_id},
    )

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    agent_config = message.agent_config.model_dump()
    del agent_config["agent_class"]

    forward_message_generator = MessageService.forward_message(
        thread_id=thread.id,
        agent_class=message.agent_config.agent_class,
        agent_config=agent_config,
        input_content=message.content,
        headers=dict(request.headers),
    )

    async def stream() -> AsyncGenerator[str, None]:
        max_chunk_size = 4096 - 32  # 4096 is the max chunk size for SSE, 32 is extra padding for the event metadata.
        chunk_count = 0

        try:
            async for chunk in forward_message_generator:
                yield create_sse_event("start", json.dumps({"chunk_id": chunk_count}))

                data = chunk.model_dump_json()
                while len(data) > max_chunk_size:
                    yield create_sse_event("delta", data[:max_chunk_size])
                    data = data[max_chunk_size:]

                yield create_sse_event("end", json.dumps({"chunk_id": chunk_count}))

                chunk_count += 1

        except Exception as e:
            logger.exception("Error in SSE stream", exc_info=e)
            sse_event = create_sse_event("error", json.dumps({"detail": str(e)[:max_chunk_size]}))
            logger.warning(f"Sending sse error event to client: {sse_event}")
            yield sse_event

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Transfer-Encoding": "chunked",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete(
    "/threads/{thread_id}/messages/{message_id}",
    tags=["messages"],
    name="delete_message",
)
async def delete_message(
    thread_id: str = Path(
        ...,
        description="The unique identifier of the thread. Can be either the internal ID or external ID.",
    ),
    message_id: str = Path(..., description="The unique identifier of the message."),
) -> Response:
    await prisma.messages.delete_many(
        where={
            "AND": [
                {"id": message_id},
                {"thread_id": thread_id},
            ],
        }
    )

    return Response(status_code=204)
