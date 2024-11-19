from fastapi import APIRouter

from src.db.prisma import prisma

router = APIRouter()


@router.get("/v1/chats", tags=["chats"])
async def get_chat(chat_id: str):
    return await prisma.chat.find_unique(where={"id": chat_id})


@router.post("/v1/chats", tags=["chats"])
async def create_chat(chat):
    return {"message": "Hello World"}
