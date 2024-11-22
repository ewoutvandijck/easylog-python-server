FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ADD . /app

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app

RUN uv sync --frozen

RUN uv run prisma db push

EXPOSE 8000

CMD ["uv", "run", "fastapi", "run", "src/main.py", "--port", "8000"]
