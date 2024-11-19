from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.v1 import chats
from src.db.prisma import prisma


@asynccontextmanager
async def lifespan(_: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()


app = FastAPI(lifespan=lifespan)

app.include_router(chats.router)
