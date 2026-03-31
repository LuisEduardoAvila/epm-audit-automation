"""File-based token storage backend.

Stores tokens in plain files under ~/.epm/tokens/{app_id}.token
"""

import logging
import os
from pathlib import Path
from typing import Optional

from epm_audit_cli.auth.backend import AuthBackend

logger = logging.getLogger(__name__)


class FileBackend(AuthBackend):
    """
    Token storage backend using local files.

    Tokens are stored in plain files under:
    ~/.epm/tokens/{app_id}.token

    This is a fallback for systems without keyring support.
    Note: Tokens are stored in plain text - use keyring when available.
    """

    TOKEN_DIR = "~/.epm/tokens"
    TOKEN_FILE_EXT = ".token"

    def __init__(self, token_dir: Optional[str] = None):
        """
        Initialize the file backend.

        Args:
            token_dir: Optional custom token directory path.
                       Defaults to ~/.epm/tokens
        """
        self._token_dir = Path(token_dir or self.TOKEN_DIR).expanduser()
        self._ensure_token_dir()

    def _ensure_token_dir(self) -> None:
        """Ensure the token directory exists."""
        self._token_dir.mkdir(parents=True, exist_ok=True)

    def _get_token_path(self, app_id: str) -> Path:
        """Get the path to the token file for an app."""
        # Sanitize app_id for use as filename
        safe_app_id = app_id.replace("/", "_").replace(":", "_")
        return self._token_dir / f"{safe_app_id}{self.TOKEN_FILE_EXT}"

    def get_token(self, app_id: str) -> Optional[str]:
        """
        Retrieve a token from file storage.

        Args:
            app_id: The application identifier.

        Returns:
            The stored token, or None if not found.
        """
        token_path = self._get_token_path(app_id)

        if not token_path.exists():
            logger.debug(f"Token file not found for {app_id}")
            return None

        try:
            token = token_path.read_text().strip()
            logger.debug(f"Retrieved token for {app_id} from file")
            return token if token else None
        except Exception as e:
            logger.warning(f"Failed to read token from file: {e}")
            return None

    def set_token(self, app_id: str, token: str) -> None:
        """
        Store a token in file storage.

        Args:
            app_id: The application identifier.
            token: The token to store.
        """
        token_path = self._get_token_path(app_id)

        try:
            # Ensure directory exists
            self._ensure_token_dir()

            # Write token (use write for atomic operation)
            token_path.write_text(token)
            logger.debug(f"Stored token for {app_id} in file")

            # Set restrictive permissions (owner only)
            try:
                os.chmod(token_path, 0o600)
            except Exception:
                # May fail on some filesystems
                pass

        except Exception as e:
            logger.warning(f"Failed to store token in file: {e}")

    def delete_token(self, app_id: str) -> None:
        """
        Delete a token from file storage.

        Args:
            app_id: The application identifier.
        """
        token_path = self._get_token_path(app_id)

        try:
            if token_path.exists():
                token_path.unlink()
                logger.debug(f"Deleted token for {app_id} from file")
        except Exception as e:
            logger.warning(f"Failed to delete token file: {e}")

    def has_token(self, app_id: str) -> bool:
        """
        Check if a token file exists.

        Args:
            app_id: The application identifier.

        Returns:
            True if token file exists, False otherwise.
        """
        return self._get_token_path(app_id).exists()

    def list_tokens(self) -> list[str]:
        """
        List all stored application IDs.

        Returns:
            List of app IDs with stored tokens.
        """
        if not self._token_dir.exists():
            return []

        tokens = []
        for token_file in self._token_dir.glob(f"*{self.TOKEN_FILE_EXT}"):
            app_id = token_file.stem  # Remove .token extension
            tokens.append(app_id)

        return tokens

    @property
    def name(self) -> str:
        """Return the backend name."""
        return "FileBackend"

    @property
    def token_dir(self) -> Path:
        """Return the token directory path."""
        return self._token_dir

    def __repr__(self) -> str:
        return f"<FileBackend dir={self._token_dir}>"