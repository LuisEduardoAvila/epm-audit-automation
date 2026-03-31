"""Abstract base class for token storage backends."""

from abc import ABC, abstractmethod
from typing import Optional


class AuthBackend(ABC):
    """
    Abstract base class for authentication token storage backends.

    All token storage implementations must inherit from this class
    and implement the required methods.
    """

    @abstractmethod
    def get_token(self, app_id: str) -> Optional[str]:
        """
        Retrieve a token for the specified application.

        Args:
            app_id: The application identifier (e.g., 'fccs_prod', 'epm_basic')

        Returns:
            The stored token string, or None if not found.
        """
        pass

    @abstractmethod
    def set_token(self, app_id: str, token: str) -> None:
        """
        Store a token for the specified application.

        Args:
            app_id: The application identifier.
            token: The token string to store.
        """
        pass

    @abstractmethod
    def delete_token(self, app_id: str) -> None:
        """
        Delete a token for the specified application.

        Args:
            app_id: The application identifier.
        """
        pass

    @abstractmethod
    def has_token(self, app_id: str) -> bool:
        """
        Check if a token exists for the specified application.

        Args:
            app_id: The application identifier.

        Returns:
            True if a token exists, False otherwise.
        """
        pass

    @property
    def name(self) -> str:
        """Return the backend name for logging purposes."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"<{self.name}>"