"""Auth endpoint Pydantic schemas (request/response models)."""

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """Login request body."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Access token response body (refresh token goes in HttpOnly cookie)."""

    access_token: str
    token_type: str = "bearer"


class UserProfileResponse(BaseModel):
    """Current user profile for GET /auth/me."""

    id: int
    email: str
    first_name: str
    last_name: str
    tenant_id: int
    branch_ids: list[int]
    roles: list[str]
    is_superadmin: bool


class ErrorResponse(BaseModel):
    """Standard error response body."""

    detail: str
    code: str | None = None
    retry_after: int | None = None
