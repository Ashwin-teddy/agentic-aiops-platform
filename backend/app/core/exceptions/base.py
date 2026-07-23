from __future__ import annotations


class AIOpsException(Exception):
    def __init__(self, message: str = "An error occurred", code: str = "UNKNOWN_ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(self.message)


class ValidationError(AIOpsException):
    def __init__(self, message: str = "Validation failed") -> None:
        super().__init__(message, "VALIDATION_ERROR")


class NotFoundError(AIOpsException):
    def __init__(self, resource: str = "Resource") -> None:
        super().__init__(f"{resource} not found", "NOT_FOUND")


class UnauthorizedError(AIOpsException):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, "UNAUTHORIZED")


class ForbiddenError(AIOpsException):
    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message, "FORBIDDEN")


class RateLimitError(AIOpsException):
    def __init__(self) -> None:
        super().__init__("Rate limit exceeded", "RATE_LIMITED")


class ExternalServiceError(AIOpsException):
    def __init__(self, service: str, message: str = "") -> None:
        super().__init__(f"External service error ({service}): {message}", "EXTERNAL_SERVICE_ERROR")
