from fastapi import APIRouter

router = APIRouter()


@router.get("/v1/chats", tags=["chats"])
async def get_chat(chat_id: str | None = None):
    return {"message": "Hello World"}


@router.post("/v1/chats", tags=["chats"])
async def create_chat(chat):
    return {"message": "Hello World"}
