FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install build dependencies, Rust, and Cairo libraries
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libcairo2-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/* \
    && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"
ENV VIRTUAL_ENV=.venv
ENV PATH="/.venv/bin:/root/.cargo/bin:${PATH}"

# Set up dependencies first
WORKDIR /app
COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

# Copy schema and generate prisma client after dependencies are cached
COPY schema.prisma ./
RUN uv run prisma generate

# Finally, copy source code
COPY src/ ./src/

ENTRYPOINT ["uv", "run"]