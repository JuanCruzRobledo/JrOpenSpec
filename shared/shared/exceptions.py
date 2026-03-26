"""Domain-specific exceptions for the Integrador application."""


class AppError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str = "An application error occurred", detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(self.message)


class DuplicateError(AppError):
    """Raised when attempting to create a duplicate resource."""

    def __init__(self, message: str = "Resource already exists", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found", detail: str | None = None):
        super().__init__(message=message, detail=detail)


class ValidationError(AppError):
    """Raised when input validation fails at the domain level."""

    def __init__(self, message: str = "Validation error", detail: str | None = None):
        super().__init__(message=message, detail=detail)
