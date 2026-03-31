"""Environment variable-based token storage backend.

Reads tokens from environment variables in the format:
EPM_TOKEN_{APP_ID}

Where {APP_ID} is the application ID in uppercase with dashes replaced by underscores.
"""

import logging
import os
import re
from typing import Optional

from epm_audit_cli.auth.backend import AuthBackend

logger = logging.getLogger(__name__)


class EnvBackend(AuthBackend):
    """
    Token storage backend using environment variables.

    Tokens are read from environment variables with the format:
    EPM_TOKEN_{APP_ID}

    Examples:
    - App ID: fccs_prod -> Env Var: EPM_TOKEN_FCCS_PROD
    - App ID: epm-basic -> Env Var: EPM_TOKEN_EPM_BASIC
    - App ID: myapp/v1 -> Env Var: EPM_TOKEN_MYAPP_V1

    This is a fallback for CI/CD environments or container deployments.
    """

    ENV_PREFIX = "EPM_TOKEN_"

    def __init__(self):
        """Initialize the env backend."""
        pass

    def _sanitize_app_id(self, app_id: str) -> str:
        """
        Convert app_id to environment variable format.

        - Convert to uppercase
        - Replace dashes with underscores
        - Replace slashes with underscores

        Args:
            app_id: The application identifier.

        Returns:
            Sanitized app ID suitable for env var name.
        """
        return app_id.upper().replace("-", "_").replace("/", "_")

    def _get_env_var_name(self, app_id: str) -> str:
        """Get the environment variable name for an app."""
        return f"{self.ENV_PREFIX}{self._sanitize_app_id(app_id)}"

    def get_token(self, app_id: str) -> Optional[str]:
        """
        Retrieve a token from environment variable.

        Args:
            app_id: The application identifier.

        Returns:
            The token from environment, or None if not set.
        """
        env_var = self._get_env_var_name(app_id)
        token = os.environ.get(env_var)

        if token:
            logger.debug(f"Retrieved token for {app_id} from env var {env_var}")
        else:
            logger.debug(f"Env var {env_var} not set for {app_id}")

        return token

    def set_token(self, app_id: str, token: str) -> None:
        """
        Set a token in environment variable.

        Note: This only updates os.environ for the current process.
        It does NOT persistently set the environment variable.

        Args:
            app_id: The application identifier.
            token: The token to set.
        """
        env_var = self._get_env_var_name(app_id)
        os.environ[env_var] = token
        logger.debug(f"Set token for {app_id} in env var {env_var}")

    def delete_token(self, app_id: str) -> None:
        """
        Delete a token from environment variable.

        Note: This only removes from os.environ for the current process.

        Args:
            app_id: The application identifier.
        """
        env_var = self._get_env_var_name(app_id)
        if env_var in os.environ:
            del os.environ[env_var]
            logger.debug(f"Deleted token for {app_id} from env var {env_var}")

    def has_token(self, app_id: str) -> bool:
        """
        Check if an environment variable is set.

        Args:
            app_id: The application identifier.

        Returns:
            True if env var is set, False otherwise.
        """
        env_var = self._get_env_var_name(app_id)
        return env_var in os.environ and bool(os.environ[env_var])

    def list_tokens(self) -> list[str]:
        """
        List all app IDs with tokens set in environment.

        Returns:
            List of app IDs with tokens in environment.
        """
        prefix = self.ENV_PREFIX
        tokens = []

        for env_var in os.environ:
            if env_var.startswith(prefix):
                # Extract app_id from env var name
                app_id_raw = env_var[len(prefix):]
                # Convert back to original format (lowercase, keep dashes/slashes)
                # This is approximate - the format is ambiguous
                app_id = app_id_raw.lower().replace("_", "-")
                tokens.append(app_id)

        return tokens

    @property
    def name(self) -> str:
        """Return the backend name."""
        return "EnvBackend"

    def __repr__(self) -> str:
        return f"<EnvBackend prefix={self.ENV_PREFIX}>"