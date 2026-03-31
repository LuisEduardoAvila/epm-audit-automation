"""
Configuration loader for EPM Audit CLI.

Reads application configuration from applications.yaml and integrates
with the credential manager for authentication.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Loads and provides access to application configuration.

    Reads applications.yaml and provides methods to access application
    configurations, OAuth settings, and environment metadata.
    """

    def __init__(self, config_path: str) -> None:
        """
        Initialize configuration loader.

        Args:
            config_path: Path to applications.yaml file

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file"""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}"
            )

        with open(self.config_path) as f:
            self._config = yaml.safe_load(f)

        logger.debug(f"Loaded configuration from {self.config_path}")

    def getApplications(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all applications configuration.

        Returns:
            Dictionary of application ID to configuration
        """
        return self._config.get("applications", {})

    def getApplication(self, app_id: str) -> Dict[str, Any]:
        """
        Get configuration for a specific application.

        Args:
            app_id: Application ID (e.g., 'fccs_prod')

        Returns:
            Application configuration dictionary

        Raises:
            KeyError: If application not found
        """
        apps = self.getApplications()
        if app_id not in apps:
            raise KeyError(
                f"Application '{app_id}' not found in configuration. "
                f"Available apps: {list(apps.keys())}"
            )
        return apps[app_id]

    def get_application(self, app_id: str) -> Dict[str, Any]:
        """
        Get configuration for a specific application (snake_case alias).

        Args:
            app_id: Application ID (e.g., 'fccs_prod')

        Returns:
            Application configuration dictionary

        Raises:
            KeyError: If application not found
        """
        return self.getApplication(app_id)

    def get_applications(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all applications configuration (snake_case alias).

        Returns:
            Dictionary of application ID to configuration
        """
        return self.getApplications()

    def list_applications(self) -> List[Dict[str, Any]]:
        """
        List all applications with basic info.

        Returns:
            List of application info dictionaries with id, name, type, sox_relevant
        """
        return [
            {
                "id": app_id,
                "name": app.get("name"),
                "type": app.get("type"),
                "sox_relevant": app.get("metadata", {}).get("sox_relevant", False),
            }
            for app_id, app in self.getApplications().items()
        ]

    def getApplicationIds(self) -> List[str]:
        """Get list of all configured application IDs"""
        return list(self.getApplications().keys())

    def getEnvironment(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Get environment metadata for an application.

        Args:
            app_id: Application ID

        Returns:
            Environment metadata dictionary or None
        """
        app = self.getApplication(app_id)
        env_id = app.get("environment")
        if env_id:
            return self._config.get("environments", {}).get(env_id)
        return None

    def getTypeMetadata(self, app_id: str) -> Optional[Dict[str, Any]]:
        """
        Get application type metadata.

        Args:
            app_id: Application ID

        Returns:
            Type metadata dictionary or None
        """
        app = self.getApplication(app_id)
        type_id = app.get("type")
        if type_id:
            return self._config.get("types", {}).get(type_id)
        return None

    def getOAuthConfig(self, scope: str) -> Dict[str, Any]:
        """
        Get OAuth configuration for a scope.

        Args:
            scope: OAuth scope name (e.g., 'production_suite')

        Returns:
            OAuth configuration dictionary

        Raises:
            KeyError: If scope not found
        """
        oauth_config = self._config.get("oauth", {})
        if scope not in oauth_config:
            raise KeyError(f"OAuth scope '{scope}' not defined in configuration")
        return oauth_config[scope]

    def getConnectionURL(self, app_id: str) -> str:
        """
        Get base connection URL for an application.

        Args:
            app_id: Application ID

        Returns:
            Base URL string
        """
        app = self.getApplication(app_id)
        return app.get("connection", {}).get("base_url", "")

    def getRegion(self, app_id: str) -> str:
        """
        Get OCI region for an application.

        Args:
            app_id: Application ID

        Returns:
            Region identifier
        """
        app = self.getApplication(app_id)
        return app.get("connection", {}).get("region", "us-phoenix-1")

    def isSOXRelevant(self, app_id: str) -> bool:
        """
        Check if application is SOX-relevant.

        Args:
            app_id: Application ID

        Returns:
            True if SOX-relevant
        """
        app = self.getApplication(app_id)
        return app.get("metadata", {}).get("sox_relevant", False)

    def getAuditEndpoints(self, app_id: str) -> List[str]:
        """
        Get available audit endpoints for an application.

        Args:
            app_id: Application ID

        Returns:
            List of endpoint names
        """
        type_meta = self.getTypeMetadata(app_id)
        if type_meta:
            return type_meta.get("audit_endpoints", [])
        return []

    def listApplicationsByEnvironment(
        self, environment: str
    ) -> List[Dict[str, Any]]:
        """
        List all applications in an environment.

        Args:
            environment: Environment name (production, test, development)

        Returns:
            List of application info dictionaries
        """
        apps = []
        for app_id, app in self.getApplications().items():
            if app.get("environment") == environment:
                apps.append(
                    {
                        "id": app_id,
                        "name": app.get("name"),
                        "type": app.get("type"),
                        "sox_relevant": app.get("metadata", {}).get(
                            "sox_relevant", False
                        ),
                    }
                )
        return apps

    def listApplicationsByType(
        self, app_type: str
    ) -> List[Dict[str, Any]]:
        """
        List all applications of a type.

        Args:
            app_type: Application type (FCCS, PBCS, EDM, etc.)

        Returns:
            List of application info dictionaries
        """
        apps = []
        for app_id, app in self.getApplications().items():
            if app.get("type") == app_type:
                apps.append(
                    {
                        "id": app_id,
                        "name": app.get("name"),
                        "environment": app.get("environment"),
                        "sox_relevant": app.get("metadata", {}).get(
                            "sox_relevant", False
                        ),
                    }
                )
        return apps