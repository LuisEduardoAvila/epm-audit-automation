"""Keyring-based token storage backend.

Uses the system keyring (keyring library) for secure token storage.
The service name format is: epm-audit-cli://{app_id}
"""

import logging
from typing import Optional

from epm_audit_cli.auth.backend import AuthBackend

logger = logging.getLogger(__name__)

# Try to import keyring, but make it optional
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    keyring = None


class KeyringBackend(AuthBackend):
    """
    Token storage backend using system keyring.

    This backend stores tokens securely in the operating system's
    credential manager (e.g., Windows Credential Manager, macOS Keychain,
    Linux Secret Service).

    The service name format is: epm-audit-cli://{app_id}
    """

    SERVICE_PREFIX = "epm-audit-cli"

    def __init__(self):
        """Initialize the keyring backend."""
        self._available = KEYRING_AVAILABLE

    @property
    def is_available(self) -> bool:
        """Check if keyring is available on this system."""
        return self._available

    def _get_service_name(self, app_id: str) -> str:
        """Get the full service name for the keyring."""
        return f"{self.SERVICE_PREFIX}://{app_id}"

    def get_token(self, app_id: str) -> Optional[str]:
        """
        Retrieve a token from keyring.

        Args:
            app_id: The application identifier.

        Returns:
            The stored token, or None if not found or keyring unavailable.
        """
        if not self._available:
            logger.debug("Keyring not available, skipping")
            return None

        try:
            service = self._get_service_name(app_id)
            token = keyring.get_password(service, app_id)
            if token:
                logger.debug(f"Retrieved token for {app_id} from keyring")
            return token
        except Exception as e:
            logger.warning(f"Failed to get token from keyring: {e}")
            return None

    def set_token(self, app_id: str, token: str) -> None:
        """
        Store a token in keyring.

        Args:
            app_id: The application identifier.
            token: The token to store.
        """
        if not self._available:
            logger.debug("Keyring not available, skipping store")
            return

        try:
            service = self._get_service_name(app_id)
            keyring.set_password(service, app_id, token)
            logger.debug(f"Stored token for {app_id} in keyring")
        except Exception as e:
            logger.warning(f"Failed to store token in keyring: {e}")

    def delete_token(self, app_id: str) -> None:
        """
        Delete a token from keyring.

        Args:
            app_id: The application identifier.
        """
        if not self._available:
            logger.debug("Keyring not available, skipping delete")
            return

        try:
            service = self._get_service_name(app_id)
            keyring.delete_password(service, app_id)
            logger.debug(f"Deleted token for {app_id} from keyring")
        except Exception as e:
            # Keyring raises Exception if password doesn't exist
            logger.debug(f"Token for {app_id} not found in keyring: {e}")

    def has_token(self, app_id: str) -> bool:
        """
        Check if a token exists in keyring.

        Args:
            app_id: The application identifier.

        Returns:
            True if token exists, False otherwise.
        """
        return self.get_token(app_id) is not None

    @property
    def name(self) -> str:
        """Return the backend name."""
        return "KeyringBackend"

    def __repr__(self) -> str:
        status = "available" if self._available else "unavailable"
        return f"<KeyringBackend ({status})>"