# syntax=docker/dockerfile:1

ARG PY_VERSION="3.14.5"
ARG UV_VERSION="0.11.15"

# UV image stage
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

# -- Builder Stage --
FROM python:${PY_VERSION}-slim-trixie AS builder

ENV UV_SYSTEM_PYTHON=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

RUN --mount=from=uv,source=/uv,target=/bin/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=cache,target=/root/.cache/uv \
    uv export --frozen --no-dev --no-editable | uv pip install -r -

FROM python:${PY_VERSION}-slim-trixie AS main

ARG PY_VERSION
ARG PY_VERSION_MINOR=${PY_VERSION%.*}

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder \
  /usr/local/lib/python${PY_VERSION_MINOR}/site-packages \
  /usr/local/lib/python${PY_VERSION_MINOR}/site-packages

COPY --from=builder /usr/local/bin /usr/local/bin

# See https://docs.docker.com/go/dockerfile-user-best-practices/
# Run the application.
CMD ["python", "main.py"]