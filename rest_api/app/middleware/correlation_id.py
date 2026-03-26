"""Correlation ID middleware — generates or forwards X-Request-ID for log tracing.

Implements REQ-SEC-04:
- If the incoming request has X-Request-ID, forward it
- Otherwise, generate a new UUID4
- Always include X-Request-ID in the response
"""

import logging
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

_HEADER_NAME = "X-Request-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Generate or forward a correlation ID on every request/response."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Use existing header or generate a new one
        request_id = request.headers.get(_HEADER_NAME) or str(uuid.uuid4())

        # Store on request state for downstream access (logging, etc.)
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[_HEADER_NAME] = request_id

        return response
