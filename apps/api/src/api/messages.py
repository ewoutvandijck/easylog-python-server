import json
from typing import Literal

from fastapi import APIRouter, HTTPException, Path, Query
from fastapi.responses import StreamingResponse
from prisma.models import Messages

from src.db.prisma import prisma
from src.logger import logger
from src.models.messages import MessageContent, MessageCreateInput
from src.models.pagination import Pagination
from src.services.message_service import MessageService
from src.utils.sse import create_sse_event

router = APIRouter()


@router.get(
    "/threads/{thread_id}/messages",
    name="get_messages",
    tags=["messages"],
    response_model=Pagination[Messages],
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
):
    messages = prisma.messages.find_many(
        where={
            "OR": [
                {"thread_id": thread_id},
                {"thread": {"is": {"external_id": thread_id}}},
            ],
        },
        order=[{"created_at": order}],
        include={"contents": True},
        take=limit,
        skip=offset,
    )

    return Pagination(data=messages, limit=limit, offset=offset)


@router.post(
    "/threads/{thread_id}/messages",
    name="create_message",
    tags=["messages"],
    response_model=MessageContent,
    response_description="A stream of JSON-encoded message chunks",
    description="Creates a new message in the given thread. Will interact with the agent and return a stream of message chunks.",
)
async def create_message(
    message: MessageCreateInput,
    thread_id: str = Path(
        ...,
        description="The unique identifier of the thread. Can be either the internal ID or external ID.",
    ),
):
    thread = prisma.threads.find_first(
        where={
            "OR": [
                {"id": thread_id},
                {"external_id": thread_id},
            ],
        },
    )

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    agent_config = message.agent_config.model_dump()
    del agent_config["agent_class"]

    forward_message_generator = MessageService.forward_message(
        thread_id=thread.id,
        agent_class=message.agent_config.agent_class,
        agent_config=agent_config,
        content=message.content,
    )

    async def stream():
        try:
            for chunk in forward_message_generator:
                yield create_sse_event("delta", chunk.model_dump_json())
        except Exception as e:
            logger.exception("Error in SSE stream", exc_info=e)
            yield create_sse_event("error", json.dumps({"detail": str(e)}))

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
    )


@router.delete(
    "/threads/{thread_id}/messages/{message_id}",
    tags=["messages"],
    name="delete_message",
)
async def delete_message(
    # TODO: Validate the user has permission to delete the message
    thread_id: str = Path(
        ...,
        description="The unique identifier of the thread. Can be either the internal ID or external ID.",
    ),
    message_id: str = Path(..., description="The unique identifier of the message."),
):
    return prisma.messages.delete(where={"id": message_id})
