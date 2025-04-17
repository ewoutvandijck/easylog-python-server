import asyncio
import time
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import health, knowledge, messages, threads
from src.lib.graphiti import graphiti
from src.lib.prisma import prisma
from src.logger import logger
from src.security.api_token import verify_api_key
from src.security.optional_http_bearer import optional_bearer_header
from src.settings import settings

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await graphiti.driver.verify_connectivity()
        await graphiti.build_indices_and_constraints()
    except Exception as e:
        logger.warning(f"Error verifying connectivity or building indices and constraints: {e}")

    await prisma.connect()
    yield
    await prisma.disconnect()

    await graphiti.close()


app = FastAPI(
    openapi_version="3.0.3",
    root_path=settings.API_ROOT_PATH,
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key), Depends(optional_bearer_header)],
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
async def add_process_time_header(request: Request, call_next: Callable[[Request], Awaitable[Response]]):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def timeout_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]):
    try:
        async with asyncio.timeout(90):  # 90 second timeout
            response = await call_next(request)
            return response
    except TimeoutError:
        return JSONResponse(status_code=504, content={"detail": "Request timeout"})


@app.middleware("http")
async def log_requests(request: Request, call_next: Callable[[Request], Awaitable[Response]]):
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
