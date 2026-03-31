"""Token manager that coordinates multiple auth backends.

The TokenManager tries backends in order: keyring > file > env
This provides a balance of security (keyring) and reliability (fallbacks).
"""

import logging
from typing import Optional, Sequence

from epm_audit_cli.auth.backend import AuthBackend
from epm_audit_cli.auth.keyring_backend import KeyringBackend
from epm_audit_cli.auth.file_backend import FileBackend
from epm_audit_cli.auth.env_backend import EnvBackend

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages authentication tokens across multiple backends.

    The manager tries backends in order of preference:
    1. KeyringBackend - Most secure, uses OS credential store
    2. FileBackend - Fallback to local file storage
    3. EnvBackend - Last resort for CI/CD environments

    Usage:
        manager = TokenManager()
        manager.set_token("fccs_prod", "my-token")
        token = manager.get_token("fccs_prod")
        manager.delete_token("fccs_prod")
    """

    def __init__(self, backends: Optional[Sequence[AuthBackend]] = None):
        """
        Initialize the token manager.

        Args:
            backends: Optional custom sequence of backends.
                     If None, uses default order: keyring > file > env
        """
        if backends:
            self._backends = list(backends)
        else:
            # Default backend chain: keyring > file > env
            self._backends = [
                KeyringBackend(),
                FileBackend(),
                EnvBackend(),
            ]

        logger.debug(f"Initialized TokenManager with backends: {self._backends}")

    def get_token(self, app_id: str) -> Optional[str]:
        """
        Retrieve a token for the specified application.

        Tries each backend in order until one returns a token.

        Args:
            app_id: The application identifier.

        Returns:
            The stored token, or None if not found in any backend.
        """
        for backend in self._backends:
            try:
                token = backend.get_token(app_id)
                if token:
                    logger.debug(f"Got token for {app_id} from {backend.name}")
                    return token
            except Exception as e:
                logger.warning(f"Backend {backend.name} failed to get token: {e}")

        logger.debug(f"No token found for {app_id} in any backend")
        return None

    def set_token(self, app_id: str, token: str) -> None:
        """
        Store a token for the specified application.

        Stores in all backends except EnvBackend (which doesn't persist).

        Args:
            app_id: The application identifier.
            token: The token to store.
        """
        stored_backends = []

        for backend in self._backends:
            # Skip EnvBackend for set - it doesn't persist across sessions
            if isinstance(backend, EnvBackend):
                continue

            try:
                backend.set_token(app_id, token)
                stored_backends.append(backend.name)
            except Exception as e:
                logger.warning(f"Backend {backend.name} failed to set token: {e}")

        if stored_backends:
            logger.info(f"Stored token for {app_id} in: {', '.join(stored_backends)}")
        else:
            logger.warning(f"Failed to store token for {app_id} in any backend")

    def delete_token(self, app_id: str) -> None:
        """
        Delete a token from all backends.

        Args:
            app_id: The application identifier.
        """
        for backend in self._backends:
            try:
                backend.delete_token(app_id)
            except Exception as e:
                logger.warning(f"Backend {backend.name} failed to delete token: {e}")

        logger.info(f"Deleted token for {app_id} from all backends")

    def has_token(self, app_id: str) -> bool:
        """
        Check if a token exists in any backend.

        Args:
            app_id: The application identifier.

        Returns:
            True if token exists in any backend, False otherwise.
        """
        return self.get_token(app_id) is not None

    def get_token_with_backend(self, app_id: str) -> tuple[Optional[str], str]:
        """
        Retrieve a token and indicate which backend it came from.

        Args:
            app_id: The application identifier.

        Returns:
            Tuple of (token, backend_name). Backend name is empty if not found.
        """
        for backend in self._backends:
            try:
                token = backend.get_token(app_id)
                if token:
                    return token, backend.name
            except Exception as e:
                logger.warning(f"Backend {backend.name} failed to get token: {e}")

        return None, ""

    def list_tokens(self) -> dict[str, str]:
        """
        List all tokens and their sources.

        Returns:
            Dictionary mapping app_id to backend name.
        """
        result = {}

        for backend in self._backends:
            try:
                if hasattr(backend, 'list_tokens'):
                    app_ids = backend.list_tokens()
                    for app_id in app_ids:
                        if app_id not in result:
                            result[app_id] = backend.name
            except Exception as e:
                logger.warning(f"Backend {backend.name} failed to list tokens: {e}")

        return result

    @property
    def backends(self) -> list[AuthBackend]:
        """Return the list of configured backends."""
        return self._backends

    def __repr__(self) -> str:
        return f"<TokenManager backends={self._backends}>"