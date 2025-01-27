FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV VIRTUAL_ENV=.venv

ENV PATH="/.venv/bin:/root/.cargo/bin:${PATH}"

ADD . /app

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app

RUN uv sync --frozen

# Replace sqlite with postgres
RUN sed -i 's/sqlite/postgres/g' schema.prisma

RUN uv run prisma generate

CMD ["uv", "run", "fastapi", "run", "src/main.py", "--port", "8000", "--host", "0.0.0.0", "--timeout-keep-alive", "90", "--timeout-notify", "90"]

