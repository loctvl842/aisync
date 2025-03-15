# Install uv
FROM python:3.12-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends git \
    # binutils is required for pyinstaller
    && apt-get install -y binutils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/packages/core

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1

ENV UV_LINK_MODE=copy

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=bind,source=packages/core/pyproject.toml,target=packages/core/pyproject.toml \
    --mount=type=bind,source=packages/core/README.md,target=packages/core/README.md \
    uv sync --frozen --no-install-project --no-dev

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=bind,source=packages/api/pyproject.toml,target=packages/api/pyproject.toml \
    --mount=type=bind,source=packages/api/README.md,target=packages/api/README.md \
    uv sync --frozen --no-install-project --no-dev

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=README.md,target=README.md \
    --mount=type=bind,source=packages/cli/pyproject.toml,target=packages/cli/pyproject.toml \
    --mount=type=bind,source=packages/cli/README.md,target=packages/cli/README.md \
    --mount=type=bind,source=packages/dev/pyproject.toml,target=packages/dev/pyproject.toml \
    --mount=type=bind,source=packages/dev/README.md,target=packages/dev/README.md \
    uv sync --frozen --no-install-project --no-dev

COPY . .

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --all-packages --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []
