# Stage 1: Builder — install dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

COPY shared/ ./shared/
COPY rest_api/pyproject.toml ./rest_api/

RUN pip install --no-cache-dir ./shared ./rest_api

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY shared/ ./shared/
COPY rest_api/ ./rest_api/
COPY alembic/ ./alembic/
COPY alembic.ini ./

EXPOSE 8000

CMD ["uvicorn", "rest_api.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
