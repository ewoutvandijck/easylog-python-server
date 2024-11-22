from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import health, messages, threads
from src.db.prisma import prisma
from src.security.api_token import verify_api_key
from src.settings import settings

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()


app = FastAPI(
    lifespan=lifespan,
    root_path=settings.API_SUFFIX,
    dependencies=[Depends(verify_api_key)],
)

# TODO: Remove this after we know the domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(threads.router)
app.include_router(messages.router)
