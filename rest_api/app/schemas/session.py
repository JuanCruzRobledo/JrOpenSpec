"""Pydantic schemas for session join endpoint."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SessionJoinRequest(BaseModel):
    """Request body for POST /api/sessions/join."""

    branchSlug: str = Field(..., min_length=1, max_length=100)
    tableIdentifier: str = Field(..., min_length=1, max_length=20)
    displayName: str = Field(default="", max_length=100)
    avatarColor: str = Field(default="#f97316", max_length=20)
    locale: str = Field(default="es", max_length=10)


class BranchInfo(BaseModel):
    """Branch summary returned in the session join response."""

    id: int
    name: str
    slug: str


class TableInfo(BaseModel):
    """Table summary returned in the session join response."""

    identifier: str
    displayName: str


class SessionJoinResponse(BaseModel):
    """Response body for POST /api/sessions/join."""

    token: str
    sessionId: int
    expiresAt: datetime
    branch: BranchInfo
    table: TableInfo
