"""Pydantic schemas for table token payloads and responses."""

from pydantic import BaseModel, Field


class TableTokenPayload(BaseModel):
    """Decoded payload from a verified table token."""

    branch_id: int = Field(..., description="Branch this table belongs to")
    table_id: int = Field(..., description="Table ID")
    session_id: int = Field(..., description="Active table session ID")
    exp: int = Field(..., description="Expiration timestamp (Unix)")
    iat: int = Field(..., description="Issued-at timestamp (Unix)")


class TableTokenResponse(BaseModel):
    """Response when generating a new table token."""

    token: str = Field(..., description="HMAC-SHA256 signed table token")
    expires_in: int = Field(..., description="Token lifetime in seconds")
