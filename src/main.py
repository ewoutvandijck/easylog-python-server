from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api import messages, threads
from src.db.prisma import prisma


@asynccontextmanager
async def lifespan(_: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()


app = FastAPI(lifespan=lifespan, root_path="/api/v1")


app.include_router(threads.router)
app.include_router(messages.router)
