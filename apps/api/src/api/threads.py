from typing import Literal

from fastapi import APIRouter, HTTPException, Path, Query, Response
from prisma.models import threads as PrismaThreads  # Import with alias to avoid name clash

from src.lib.prisma import prisma
from src.models.messages import Message  # Import Pydantic Message model
from src.models.pagination import Pagination
from src.models.threads import ThreadCreateInput, ThreadResponse  # Import Pydantic Thread models
from src.services.messages.utils.db_message_to_message_model import db_message_to_message_model  # Import the converter
from src.utils.is_valid_uuid import is_valid_uuid

router = APIRouter()


def transform_db_thread_to_response(db_thread: PrismaThreads) -> ThreadResponse:
    """Converts a Prisma thread object (with included messages/contents) to a ThreadResponse Pydantic model."""
    messages_response: list[Message] = []
    if db_thread.messages:
        messages_response = [db_message_to_message_model(msg) for msg in db_thread.messages if msg.contents is not None]

    return ThreadResponse(
        id=db_thread.id,
        external_id=db_thread.external_id,
        created_at=db_thread.created_at,
        updated_at=db_thread.updated_at,
        # metadata=db_thread.metadata,  # Assumes metadata is directly compatible or None
        messages=messages_response,
    )


@router.get(
    "/threads",
    name="get_threads",
    tags=["threads"],
    response_model=Pagination[ThreadResponse],  # Use Pydantic model
    description="Retrieves all threads. Returns a list of all threads with their messages by default in descending chronological order (newest first). Each message includes its full content.",
)
async def get_threads(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
    ),
    offset: int = Query(default=0, ge=0),
    order: Literal["asc", "desc"] = Query(default="desc"),
) -> Pagination[ThreadResponse]:  # Use Pydantic model
    db_threads = await prisma.threads.find_many(
        take=limit,
        skip=offset,
        order={"created_at": order},
        include={
            "messages": {
                "order_by": {"created_at": order},
                "include": {
                    "contents": True,
                },
            }
        },
    )

    # Transform data before returning
    thread_responses = [transform_db_thread_to_response(db_thread) for db_thread in db_threads]
    return Pagination(data=thread_responses, limit=limit, offset=offset)


@router.get(
    "/threads/{id}",
    name="get_thread_by_id",
    tags=["threads"],
    response_model=ThreadResponse,  # Use Pydantic model
    responses={
        404: {"description": "Thread not found"},
    },
    description="Retrieves a specific thread by its unique ID. Returns the thread details along with its messages in descending chronological order (newest first). Each message includes its full content.",
)
async def get_thread_by_id(
    _id: str = Path(
        ...,
        alias="id",
        description="The unique identifier of the thread. Can be either the internal ID or external ID.",
    ),
) -> ThreadResponse:  # Use Pydantic model
    db_thread = await prisma.threads.find_first(
        where={"id": _id} if is_valid_uuid(_id) else {"external_id": _id},
        include={
            "messages": {
                "order_by": {"created_at": "desc"},
                "include": {
                    "contents": True,
                },
            }
        },
    )

    if not db_thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Transform data before returning
    return transform_db_thread_to_response(db_thread)


@router.post(
    "/threads",
    name="create_thread",
    tags=["threads"],
    response_model=ThreadResponse,  # Use Pydantic model
    description="Creates a new thread or returns the existing thread if it already exists.",
)
async def create_thread(thread: ThreadCreateInput) -> ThreadResponse:  # Use Pydantic model
    if thread.external_id:
        result = await prisma.threads.upsert(
            where={
                "external_id": thread.external_id,
            },
            data={
                "create": {
                    "external_id": thread.external_id,
                },
                "update": {},
            },
            include={
                "messages": {
                    "order_by": {"created_at": "desc"},
                    "include": {
                        "contents": True,
                    },
                }
            },
        )
        # Transform data before returning
        return transform_db_thread_to_response(result)

    result = await prisma.threads.create(
        data={"external_id": thread.external_id},
        include={
            "messages": {
                "order_by": {"created_at": "desc"},
                "include": {
                    "contents": True,
                },
            }
        },
    )
    # Transform data before returning
    return transform_db_thread_to_response(result)


@router.delete(
    "/threads/{id}",
    name="delete_thread",
    tags=["threads"],
    description="Deletes a thread by its internal or external ID.",
)
async def delete_thread(
    _id: str = Path(
        ...,
        alias="id",
        description="The unique identifier of the thread. Can be either the internal ID or external ID.",
    ),
) -> Response:
    # Delete doesn't return data, so no change needed here
    await prisma.threads.delete_many(
        where={"id": _id} if is_valid_uuid(_id) else {"external_id": _id},
    )

    return Response(status_code=204)
