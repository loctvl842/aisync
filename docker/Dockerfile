ARG POETRY_HOME=/opt/poetry

### Builder
FROM python:3.12-slim as builder

ARG POETRY_HOME
ARG POETRY_VERSION=1.8.3

RUN python3 -m venv ${POETRY_HOME} && \
    $POETRY_HOME/bin/pip install --upgrade pip && \
    $POETRY_HOME/bin/pip install poetry==${POETRY_VERSION} \
    echo "Poetry version:" && $POETRY_HOME/bin/poetry --version


### Dependencies
FROM builder as dependencies

ARG POETRY_HOME

ENV PIP_DEFAULT_TIMEOUT=100 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="$POETRY_HOME/bin:$PATH" \
    VIRTUAL_ENV="/app/.venv"

WORKDIR /app
COPY pyproject.toml poetry.lock poetry.toml ./
COPY packages ./packages

RUN poetry install --only main --no-interaction --no-ansi --no-root

### Build
FROM python:3.12-slim as build

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

COPY --from=dependencies /app/.venv /app/.venv
COPY packages ./packages

RUN addgroup --system appgroup && \
    adduser --system --group appuser && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 8080

CMD ["python", "-m", "packages.api.aisync_api.main"]
