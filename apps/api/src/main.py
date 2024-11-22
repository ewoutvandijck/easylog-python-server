from contextlib import asynccontextmanager
from urllib.parse import urljoin

from dotenv import load_dotenv
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import health, messages, threads
from src.db.prisma import prisma
from src.logging import logger
from src.security.api_token import verify_api_key
from src.settings import settings

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()


logger.info(f"API_ROOT_PATH: {settings.API_ROOT_PATH}")


app = FastAPI(
    lifespan=lifespan,
    root_path=urljoin(settings.API_ROOT_PATH, "api/v1"),
    docs_url=urljoin(settings.API_ROOT_PATH, "docs"),
    redoc_url=urljoin(settings.API_ROOT_PATH, "redoc"),
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
