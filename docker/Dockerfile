FROM python:3.9-alpine AS builder

WORKDIR /app

COPY ./docker/install-deps.sh install-deps.sh
RUN sh install-deps.sh

COPY pyproject.toml uv.lock /app/

RUN uv sync

COPY ./server.py ./reader.py /app/
COPY ./static /app/static
COPY ./templates /app/templates

FROM python:3.9-alpine AS runner
COPY --from=builder --chown=nobody /app /app
RUN apk add libxml2 libxslt
USER nobody
WORKDIR /app
ENV FLASK_APP="server.py"
CMD ["/app/.venv/bin/flask", "run", "--port", "5000", "--host", "0.0.0.0"]
LABEL org.opencontainers.image.source="https://github.com/SnoenSoftware/europass-server"
