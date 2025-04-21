from typing import Literal

from fastapi import APIRouter, HTTPException, Path, Query, Response

from src.lib.prisma import prisma
from src.models.pagination import Pagination
from src.models.threads import ThreadCreateInput, ThreadResponse
from src.services.messages.utils.db_message_to_message_model import db_message_to_message_model
from src.utils.is_valid_uuid import is_valid_uuid

router = APIRouter()


@router.get(
    "/threads",
    name="get_threads",
    tags=["threads"],
    response_model=Pagination[ThreadResponse],
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
) -> Pagination[ThreadResponse]:
    threads = await prisma.threads.find_many(
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

    return Pagination(
        data=[
            ThreadResponse(
                **thread.model_dump(exclude={"messages"}),
                messages=[db_message_to_message_model(message) for message in thread.messages or []],
            )
            for thread in threads
        ],
        limit=limit,
        offset=offset,
    )


@router.get(
    "/threads/{id}",
    name="get_thread_by_id",
    tags=["threads"],
    response_model=ThreadResponse,
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
) -> ThreadResponse:
    thread = await prisma.threads.find_first(
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

    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    return ThreadResponse(
        **thread.model_dump(exclude={"messages"}),
        messages=[db_message_to_message_model(message) for message in thread.messages or []],
    )


@router.post(
    "/threads",
    name="create_thread",
    tags=["threads"],
    response_model=ThreadResponse,
    description="Creates a new thread or returns the existing thread if it already exists.",
)
async def create_thread(thread: ThreadCreateInput) -> ThreadResponse:
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
    else:
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

    return ThreadResponse(
        **result.model_dump(exclude={"messages"}),
        messages=[db_message_to_message_model(message) for message in result.messages or []],
    )


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
    await prisma.threads.delete_many(
        where={"id": _id} if is_valid_uuid(_id) else {"external_id": _id},
    )

    return Response(status_code=204)
