"""
Logout command for EPM Audit CLI.

Ends authentication session by clearing cached tokens.
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
        console.print("[yellow]No active sessions[/yellow]")
        return

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

    console.print("[dim]Note: Token cache cleared. Re-authenticate with 'epm login'[/dim]")