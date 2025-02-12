import asyncio
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api import health, messages, threads
from src.db.prisma import prisma
from src.security.api_token import verify_api_key
from src.security.optional_http_bearer import optional_bearer_header
from src.settings import settings

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    prisma.connect()
    yield
    prisma.disconnect()


app = FastAPI(
    root_path=settings.API_ROOT_PATH,
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key), Depends(optional_bearer_header)],
)

# TODO: Remove this after we know the domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Process-Time"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def timeout_middleware(request, call_next):
    try:
        async with asyncio.timeout(90):  # 90 second timeout
            response = await call_next(request)
            return response
    except TimeoutError:
        return JSONResponse(status_code=504, content={"detail": "Request timeout"})


app.include_router(health.router)
app.include_router(threads.router)
app.include_router(messages.router)
