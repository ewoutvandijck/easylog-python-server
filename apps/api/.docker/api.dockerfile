FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build dependencies and Rust
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"
ENV VIRTUAL_ENV=.venv
ENV PATH="/.venv/bin:/root/.cargo/bin:${PATH}"

ADD . /app

# Sync the project into a new environment, using the frozen lockfile
WORKDIR /app

RUN uv sync --frozen

ENTRYPOINT ["uv", "run", "fastapi", "run", "src/main.py", "--port", "8000", "--host", "0.0.0.0"]