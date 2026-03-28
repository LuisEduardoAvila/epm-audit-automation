"""
Login command for EPM Audit CLI.

Handles authentication to EPM Cloud applications using OAuth tokens
from the credential manager.
"""

from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from epm_audit_cli.config.loader import ConfigLoader
from epm_audit_cli.exceptions import EPMConfigurationError, EPMAuthenticationError

console = Console()


def login(
    ctx: click.Context,
    app: Optional[str],
    verify: bool,
    backend: str,
) -> None:
    """
    Authenticate to an EPM application.

    Args:
        ctx: Click context
        app: Application ID from config
        verify: Whether to verify connection after login
        backend: Credential backend to use
    """
    # Get CLI context
    cli_ctx = ctx.obj

    # If no app specified, list available apps
    if not app:
        _list_applications(cli_ctx)
        return

    # Load configuration
    config = _get_config(cli_ctx)

    # Get app config
    app_config = config.get_application(app)
    if not app_config:
        raise EPMConfigurationError(
            f"Application '{app}' not found in configuration",
            suggestion="Run 'epm login' without arguments to see available applications",
        )

    console.print(f"[cyan]Logging into {app}...[/cyan]")

    # Get credentials from credential manager
    try:
        # Import credential manager from parent project
        import sys
        from pathlib import Path
        parent_project = Path(__file__).parent.parent.parent.parent.parent / "scripts"
        sys.path.insert(0, str(parent_project))

        from credential_manager import CredentialManager

        cred_mgr = CredentialManager()

        # Get OAuth token
        token = cred_mgr.get_oauth_token(app)

        if not token:
            # Try to authenticate
            console.print("[yellow]No cached token found, authenticating...[/yellow]")
            token = cred_mgr.authenticate(app_config)

        # Store token in context
        if not hasattr(cli_ctx, 'tokens'):
            cli_ctx.tokens = {}
        cli_ctx.tokens[app] = token

        console.print(f"[green]✓[/green] Authenticated to {app}")

        if verify:
            _verify_connection(app_config, token)

    except ImportError:
        # Fallback to mock if credential manager not available
        console.print("[yellow]Warning: Credential manager not found, using mock mode[/yellow]")
        if not hasattr(cli_ctx, 'tokens'):
            cli_ctx.tokens = {}
        cli_ctx.tokens[app] = "mock_token"

        console.print(f"[green]✓[/green] Mock authenticated to {app}")

        if verify:
            console.print("[yellow]Skipping verification in mock mode[/yellow]")

    except Exception as e:
        raise EPMAuthenticationError(
            f"Authentication failed: {str(e)}",
            suggestion="Check credentials in OCI Vault or run 'epm config init'",
        )


def _list_applications(cli_ctx) -> None:
    """List available applications from config."""
    config = _get_config(cli_ctx)

    if not config:
        console.print("[yellow]No configuration loaded[/yellow]")
        console.print("Run 'epm config init' to create a configuration file")
        return

    apps = config.list_applications()

    if not apps:
        console.print("[yellow]No applications configured[/yellow]")
        return

    table = Table(title="Available Applications")
    table.add_column("App ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("URL", style="dim")

    for app_id, app_config in apps.items():
        app_type = app_config.get("type", "unknown")
        url = app_config.get("url", "N/A")
        # Truncate URL for display
        if len(url) > 50:
            url = url[:47] + "..."
        table.add_row(app_id, app_type, url)

    console.print(table)


def _get_config(cli_ctx) -> ConfigLoader:
    """Get configuration from context."""
    if cli_ctx.config:
        return cli_ctx.config

    # Try default config location
    from pathlib import Path
    default_config = Path("config/applications.yaml")

    if default_config.exists():
        return ConfigLoader(str(default_config))

    return None


def _verify_connection(app_config: dict, token: str) -> None:
    """Verify connection to EPM application."""
    from epm_audit_cli.clients.base import BaseAPIClient

    console.print("[cyan]Verifying connection...[/cyan]")

    base_url = app_config.get("url", "")
    app_id = app_config.get("id", "unknown")

    client = BaseAPIClient(base_url, token, app_id)

    try:
        info = client.verify_connection()
        console.print(f"[green]✓[/green] Connection verified")
        console.print(f"  API Version: {info.get('api_version', 'unknown')}")
        console.print(f"  Applications: {info.get('app_count', 'unknown')}")
    except Exception as e:
        console.print(f"[yellow]Warning: Connection verification failed: {e}[/yellow]")