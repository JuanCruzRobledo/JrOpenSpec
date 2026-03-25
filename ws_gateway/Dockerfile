# Stage 1: Builder — install dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

COPY shared/ ./shared/
COPY ws_gateway/pyproject.toml ./ws_gateway/

RUN pip install --no-cache-dir ./shared ./ws_gateway

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY shared/ ./shared/
COPY ws_gateway/ ./ws_gateway/

EXPOSE 8001

CMD ["uvicorn", "ws_gateway.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
