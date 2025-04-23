import asyncio
import time
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMConfig, OpenAIClient

from src.api import health, knowledge, messages, threads
from src.lib import graphiti as graphiti_lib
from src.lib.openai import openai_client
from src.lib.prisma import prisma
from src.logger import logger
from src.security.api_token import verify_api_key
from src.settings import settings

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, None]:
    try:
        graphiti_lib.graphiti_connection = Graphiti(
            user=settings.NEO4J_USER,
            password=settings.NEO4J_PASSWORD,
            uri=settings.NEO4J_URI,
            llm_client=OpenAIClient(
                config=LLMConfig(
                    api_key=settings.OPENROUTER_API_KEY,
                    base_url="https://openrouter.ai/api/v1",
                    model="openai/gpt-4.1-mini",
                ),
                client=openai_client,
            ),
        )
    except Exception as e:
        logger.warning(f"Error initializing Graphiti connection: {e}", exc_info=True)

    await prisma.connect()

    yield

    await prisma.disconnect()

    if graphiti_lib.graphiti_connection:
        await graphiti_lib.graphiti_connection.close()


app = FastAPI(
    openapi_version="3.0.3",
    root_path=settings.API_ROOT_PATH,
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def timeout_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    try:
        async with asyncio.timeout(90):  # 90 second timeout
            response = await call_next(request)
            return response
    except TimeoutError:
        return JSONResponse(status_code=504, content={"detail": "Request timeout"})


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        f"Method: {request.method} Path: {request.url.path} Status: {response.status_code} Duration: {duration:.2f}s"
    )
    return response


app.include_router(health.router)
app.include_router(threads.router)
app.include_router(messages.router)
app.include_router(knowledge.router)
