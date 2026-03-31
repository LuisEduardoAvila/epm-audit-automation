"""Token authentication backends for EPM Audit CLI.

This module provides multiple backend implementations for storing and
retrieving OAuth tokens:

- KeyringBackend: Uses system keyring (keyring library)
- FileBackend: Stores tokens in files (~/.epm/tokens/)
- EnvBackend: Reads tokens from environment variables (EPM_TOKEN_{APP_ID})

The TokenManager class tries backends in order: keyring > file > env
"""

from epm_audit_cli.auth.backend import AuthBackend
from epm_audit_cli.auth.keyring_backend import KeyringBackend
from epm_audit_cli.auth.file_backend import FileBackend
from epm_audit_cli.auth.env_backend import EnvBackend
from epm_audit_cli.auth.manager import TokenManager

__all__ = [
    "AuthBackend",
    "KeyringBackend",
    "FileBackend",
    "EnvBackend",
    "TokenManager",
]