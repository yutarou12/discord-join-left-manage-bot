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

# Create a non-privileged user that the app will run under.
# See https://docs.docker.com/go/dockerfile-user-best-practices/
ARG HOST_UID=1000
ARG HOST_GID=1000

RUN <<EOF bash -eux
if ! getent group ${HOST_GID} > /dev/null; then
    groupadd -g ${HOST_GID} appgroup;
fi
useradd -u ${HOST_UID} -g ${HOST_GID} -m appuser
# Change ownership of /src directory to appuser
chown -R appuser:appgroup .
EOF

COPY --chown=appuser:appgroup /app/ .

# Switch to the non-privileged user to run the application.
USER appuser

# Run the application.
CMD ["python", "main.py"]