from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI

from src.api import messages, threads
from src.db.prisma import prisma
from src.security import verify_api_key

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()


app = FastAPI(
    lifespan=lifespan, root_path="/api/v1", dependencies=[Depends(verify_api_key)]
)


app.include_router(threads.router)
app.include_router(messages.router)
