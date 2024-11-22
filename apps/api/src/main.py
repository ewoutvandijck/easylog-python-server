import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.api import health, messages, threads
from src.db.prisma import prisma
from src.security.api_token import verify_api_key

load_dotenv()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()


app = FastAPI(
    docs_url="/ai/docs",
    redoc_url="/ai/redoc",
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)],
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


app.include_router(health.router)
app.include_router(threads.router)
app.include_router(messages.router)
