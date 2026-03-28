"""
Custom exceptions for EPM Audit CLI.

Provides specific error types for different failure scenarios
with helpful suggestion messages.
"""

from typing import Optional


class EPMError(Exception):
    """
    Base exception for EPM CLI errors.

    Attributes:
        message: Error message
        code: HTTP status code or error code
        suggestion: Optional suggestion for user
    """

    def __init__(
        self,
        message: str,
        code: int = 500,
        suggestion: Optional[str] = None,
    ) -> None:
        self.message = message
        self.code = code
        self.suggestion = suggestion
        super().__init__(message)

    def __str__(self) -> str:
        if self.suggestion:
            return f"{self.message}\nHint: {self.suggestion}"
        return self.message


class EPMConnectionError(EPMError):
    """Connection-related errors (network, DNS, timeout)"""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
    ) -> None:
        super().__init__(message, code=503, suggestion=suggestion)


class EPMAuthenticationError(EPMError):
    """Authentication and authorization errors"""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
    ) -> None:
        super().__init__(message, code=401, suggestion=suggestion)


class EPMValidationError(EPMError):
    """Validation errors (bad request, invalid parameters)"""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
    ) -> None:
        super().__init__(message, code=400, suggestion=suggestion)


class EPMRateLimitError(EPMError):
    """Rate limiting errors"""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
    ) -> None:
        super().__init__(message, code=429, suggestion=suggestion)


class EPMNotFoundError(EPMError):
    """Resource not found errors"""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
    ) -> None:
        super().__init__(message, code=404, suggestion=suggestion)


class EPMConfigurationError(EPMError):
    """Configuration errors"""

    def __init__(
        self,
        message: str,
        suggestion: Optional[str] = None,
    ) -> None:
        super().__init__(message, code=1, suggestion=suggestion)