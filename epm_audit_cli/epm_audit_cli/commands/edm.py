"""
EDM commands for EPM Audit CLI.

Request history, request details, and policy violations.
"""

from typing import Optional
import click
from rich.console import Console
from rich.table import Table

from epm_audit_cli.config.loader import ConfigLoader
from epm_audit_cli.clients.base import BaseAPIClient
from epm_audit_cli.output import format_output
from epm_audit_cli.exceptions import EPMValidationError, EPMAuthenticationError

console = Console()


def _get_token(ctx: click.Context, app: str) -> str:
    """Get authentication token for app."""
    cli_ctx = ctx.obj
    if hasattr(cli_ctx, 'tokens') and app in cli_ctx.tokens:
        return cli_ctx.tokens[app]
    raise EPMAuthenticationError(
        f"Not authenticated to {app}",
        suggestion=f"Run 'epm login {app}' first",
    )


def _get_config(ctx: click.Context) -> ConfigLoader:
    """Get configuration."""
    cli_ctx = ctx.obj
    if cli_ctx.config:
        return cli_ctx.config
    from pathlib import Path
    default_config = Path("config/applications.yaml")
    if default_config.exists():
        return ConfigLoader(str(default_config))
    raise EPMValidationError(
        "No configuration found",
        suggestion="Run 'epm config init' to create a configuration file",
    )


def edm_requests(
    ctx: click.Context,
    app: str,
    status: Optional[str],
    from_date: Optional[str],
    to_date: Optional[str],
    output: str,
    limit: int,
) -> None:
    """List EDM request history."""
    token = _get_token(ctx, app)
    config = _get_config(ctx)
    app_config = config.get_application(app)

    if not app_config:
        raise EPMValidationError(
            f"Application '{app}' not found",
            suggestion="Check config/applications.yaml",
        )

    base_url = app_config.get("url", "")
    client = BaseAPIClient(base_url, token, app)

    console.print(f"[cyan]Querying EDM requests for {app}...[/cyan]")

    params = {}
    if status:
        params["status"] = status
    if from_date:
        params["submittedDateFrom"] = from_date
    if to_date:
        params["submittedDateTo"] = to_date

    try:
        results = client._paginated_request(
            "/edm/rest/v1/requests",
            params=params,
            limit=limit,
        )

        if output == "table":
            table = Table(title="EDM Requests")
            table.add_column("Request ID", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Submitted", style="dim")
            table.add_column("Submitted By", style="yellow")
            table.add_column("Type", style="magenta")

            for r in results[:50]:
                table.add_row(
                    r.get("requestId", r.get("id", "N/A"))[:25],
                    r.get("status", "N/A"),
                    r.get("submittedDate", "N/A")[:10],
                    r.get("submittedBy", "N/A")[:20],
                    r.get("requestType", "N/A"),
                )
            console.print(table)
        else:
            console.print(format_output(results, output))

        console.print(f"\n[green]✓[/green] Found {len(results)} requests")

    except Exception as e:
        raise EPMValidationError(
            f"Failed to query EDM requests: {str(e)}",
            suggestion="Check application ID and parameters",
        )


def edm_request(
    ctx: click.Context,
    app: str,
    request_id: str,
    output: str,
) -> None:
    """Get EDM request details."""
    token = _get_token(ctx, app)
    config = _get_config(ctx)
    app_config = config.get_application(app)

    if not app_config:
        raise EPMValidationError(f"Application '{app}' not found", suggestion="Check config/applications.yaml")

    base_url = app_config.get("url", "")
    client = BaseAPIClient(base_url, token, app)

    console.print(f"[cyan]Getting EDM request {request_id}...[/cyan]")

    try:
        result = client.get(f"/edm/rest/v1/requests/{request_id}")

        if output == "table":
            console.print(format_output(result, "json"))
        else:
            console.print(format_output(result, output))

    except Exception as e:
        raise EPMValidationError(
            f"Failed to get EDM request: {str(e)}",
            suggestion="Check request ID format (e.g., REQ-2026-0226-001)",
        )


def edm_violations(
    ctx: click.Context,
    app: str,
    from_date: Optional[str],
    to_date: Optional[str],
    severity: Optional[str],
    output: str,
    limit: int,
) -> None:
    """List EDM policy violations."""
    token = _get_token(ctx, app)
    config = _get_config(ctx)
    app_config = config.get_application(app)

    if not app_config:
        raise EPMValidationError(f"Application '{app}' not found", suggestion="Check config/applications.yaml")

    base_url = app_config.get("url", "")
    client = BaseAPIClient(base_url, token, app)

    console.print(f"[cyan]Querying EDM violations for {app}...[/cyan]")

    params = {}
    if from_date:
        params["fromDate"] = from_date
    if to_date:
        params["toDate"] = to_date
    if severity:
        params["severity"] = severity

    try:
        results = client._paginated_request(
            "/edm/rest/v1/policies/violations",
            params=params,
            limit=limit,
        )

        if output == "table":
            table = Table(title="EDM Policy Violations")
            table.add_column("Violation ID", style="cyan")
            table.add_column("Severity", style="red")
            table.add_column("Policy", style="yellow")
            table.add_column("Status", style="green")
            table.add_column("Date", style="dim")

            for r in results[:50]:
                table.add_row(
                    r.get("violationId", r.get("id", "N/A"))[:25],
                    r.get("severity", "N/A"),
                    r.get("policyName", "N/A")[:30],
                    r.get("status", "N/A"),
                    r.get("violationDate", "N/A")[:10],
                )
            console.print(table)
        else:
            console.print(format_output(results, output))

        console.print(f"\n[green]✓[/green] Found {len(results)} violations")

    except Exception as e:
        raise EPMValidationError(
            f"Failed to query violations: {str(e)}",
            suggestion="Check application ID and date range",
        )