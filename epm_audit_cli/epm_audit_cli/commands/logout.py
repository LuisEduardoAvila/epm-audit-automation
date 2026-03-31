"""
Logout command for EPM Audit CLI.

Ends authentication session by clearing cached tokens from both
CLI context and the token manager backends.
"""

from typing import Optional
import click
from rich.console import Console

from epm_audit_cli.exceptions import EPMConfigurationError

console = Console()


def logout(ctx: click.Context, logout_all: bool) -> None:
    """
    End authentication session.

    Args:
        ctx: Click context
        logout_all: Whether to logout from all applications
    """
    cli_ctx = ctx.obj

    if not hasattr(cli_ctx, 'tokens') or not cli_ctx.tokens:
        # Try to clear from token manager even if no context tokens
        _clear_token_manager_tokens(cli_ctx)
        console.print("[yellow]No active sessions[/yellow]")
        return

    # Clear from token manager backends (keyring, file, env)
    _clear_token_manager_tokens(cli_ctx)

    if logout_all:
        count = len(cli_ctx.tokens)
        cli_ctx.tokens.clear()
        console.print(f"[green]✓[/green] Logged out from {count} application(s)")
    else:
        # Logout from current app (first in dict)
        if cli_ctx.tokens:
            app = list(cli_ctx.tokens.keys())[0]
            del cli_ctx.tokens[app]
            console.print(f"[green]✓[/green] Logged out from {app}")

    console.print("[dim]Note: Token cache and stored tokens cleared. Re-authenticate with 'epm login'[/dim]")


def _clear_token_manager_tokens(cli_ctx) -> None:
    """Clear tokens from token manager backends."""
    token_mgr = getattr(cli_ctx, 'token_manager', None)

    if not token_mgr:
        return

    # Get all apps we're logged into from context
    apps = getattr(cli_ctx, 'tokens', {}).keys()

    for app in apps:
        try:
            token_mgr.delete_token(app)
        except Exception as e:
            # Non-fatal - just log
            console.print(f"[dim]Warning: Could not clear token for {app}: {e}[/dim]")