FROM registry.access.redhat.com/ubi9/python-39:latest AS base


FROM base AS builder
COPY --from=ghcr.io/astral-sh/uv:0.4.9 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /opt/app-root/src
COPY uv.lock pyproject.toml /opt/app-root/src/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-install-project --no-dev
COPY ./8Knot/ /opt/app-root/src/
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev


FROM base
COPY --from=builder /opt/app-root/src /opt/app-root/src
ENV PATH="/opt/app-root/src/.venv/bin:$PATH"

# Explicitly tell Python where to find packages
ENV PYTHONPATH="/opt/app-root/src/.venv/lib/python3.9/site-packages:/opt/app-root/src"

# Description of how to choose the number of workers and threads.
# common wisdom is (2*CPU)+1 workers:
# https://medium.com/building-the-system/gunicorn-3-means-of-concurrency-efbb547674b7
# this is a microservice - above may not apply
CMD [ "gunicorn", "--bind", ":8080", "app:server", "--workers", "1", "--threads", "2" ]
