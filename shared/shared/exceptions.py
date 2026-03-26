"""Domain-specific exceptions for the Integrador application."""


class AppError(Exception):
    """Base exception for all application errors.

    All subclasses carry an HTTP status_code so exception handlers can
    map them to the correct response without a lookup table.
    """

    status_code: int = 500

    def __init__(self, message: str = "An application error occurred", detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


# --- 4xx Client Errors ---


class AuthenticationError(AppError):
    """Raised when authentication fails (invalid credentials, expired token, etc.)."""

    status_code = 401

    def __init__(self, message: str = "Authentication failed", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class ForbiddenError(AppError):
    """Raised when an authenticated user lacks permission for the requested action."""

    status_code = 403

    def __init__(self, message: str = "Forbidden", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class BranchAccessError(ForbiddenError):
    """Raised when a user tries to access a branch they are not assigned to."""

    def __init__(self, message: str = "Branch access denied", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class InsufficientRoleError(ForbiddenError):
    """Raised when a user's role is insufficient for the requested operation."""

    def __init__(self, message: str = "Insufficient role", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""

    status_code = 404

    def __init__(self, message: str = "Resource not found", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class ConflictError(AppError):
    """Raised on state conflicts (e.g. duplicate resource, invalid state transition)."""

    status_code = 409

    def __init__(self, message: str = "Conflict", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class DuplicateError(ConflictError):
    """Raised when attempting to create a duplicate resource."""

    def __init__(self, message: str = "Resource already exists", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class InvalidStateError(ConflictError):
    """Raised when an operation is invalid for the current resource state."""

    def __init__(self, message: str = "Invalid state transition", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class ValidationError(AppError):
    """Raised when input validation fails at the domain level."""

    status_code = 422

    def __init__(self, message: str = "Validation error", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class RateLimitError(AppError):
    """Raised when a client exceeds the allowed request rate."""

    status_code = 429

    def __init__(self, message: str = "Too many requests", detail: str | None = None):
        super().__init__(message=message, detail=detail)


# --- 5xx Server Errors ---


class DatabaseError(AppError):
    """Raised on unrecoverable database errors."""

    status_code = 500

    def __init__(self, message: str = "Database error", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class InternalError(AppError):
    """Raised for unexpected internal server errors."""

    status_code = 500

    def __init__(self, message: str = "Internal server error", detail: str | None = None):
        super().__init__(message=message, detail=detail)
