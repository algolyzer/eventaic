from fastapi import HTTPException, status
from typing import Any, Optional, Dict


class EventaicException(HTTPException):
    """Base exception class for Eventaic"""

    def __init__(
            self,
            status_code: int,
            detail: Any = None,
            headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class AuthenticationException(EventaicException):
    """Raised when authentication fails"""

    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationException(EventaicException):
    """Raised when user lacks required permissions"""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundException(EventaicException):
    """Raised when requested resource is not found"""

    def __init__(self, resource: str = "Resource"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} not found"
        )


class ValidationException(EventaicException):
    """Raised when validation fails"""

    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class RateLimitException(EventaicException):
    """Raised when rate limit is exceeded"""

    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )


class DifyAPIException(EventaicException):
    """Raised when Dify API call fails"""

    def __init__(self, detail: str = "External API error"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class DatabaseException(EventaicException):
    """Raised when database operation fails"""

    def __init__(self, detail: str = "Database error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class EmailException(EventaicException):
    """Raised when email operation fails"""

    def __init__(self, detail: str = "Email service error"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class CompanyLimitException(EventaicException):
    """Raised when company exceeds limits"""

    def __init__(self, detail: str = "Company limit exceeded"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )
