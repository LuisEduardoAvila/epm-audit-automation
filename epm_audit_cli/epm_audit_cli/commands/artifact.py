"""
Artifact changes command for EPM Audit CLI.

Query artifact modification history for SOX audit trails.
"""

from typing import List, Optional
import click
from rich.console import Console
from datetime import datetime

from epm_audit_cli.config.loader import ConfigLoader
from epm_audit_cli.clients.base import BaseAPIClient
from epm_audit_cli.output import format_output
from epm_audit_cli.exceptions import EPMValidationError, EPMAuthenticationError

console = Console()


# Artifact type classification
MATERIAL_TYPES = {
    'CONSOLIDATION_RULE', 'BUSINESS_RULE', 'CALCULATION_RULE',
    'DATA_FORM', 'COMPOSITE_FORM', 'DIMENSION', 'ATTRIBUTE',
    'SMART_LIST', 'SUBSTITUTION_VARIABLE', 'CURRENCY_TABLE',
    'ALLOCATION_RULE', 'RECONCILIATION_FORMAT', 'MATCHING_RULE',
    'VALIDATION_RULE', 'DATA_LOAD_RULE', 'IMPORT_FORMAT'
}

OPERATIONAL_TYPES = {
    'PERIOD', 'PERIOD_STATUS', 'JOB', 'CONSOLIDATION_EXECUTION',
    'JOURNAL_POSTING', 'FORM_SAVE', 'DATA_ENTRY', 'CALCULATION_RUN',
    'APPROVAL_PROMOTION', 'REQUEST_APPROVAL', 'SNAPSHOT_RESTORE',
    'BACKUP', 'REPLICATION'
}


def artifact_changes(
    ctx: click.Context,
    app: str,
    from_date: str,
    to_date: str,
    artifact_types: List[str],
    modified_by: Optional[str],
    modified_by_exclude: Optional[str],
    output: str,
    limit: int,
) -> None:
    """
    Query artifact modification history.

    Args:
        ctx: Click context
        app: Application ID
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        artifact_types: Filter by artifact types
        modified_by: Filter by user
        modified_by_exclude: Exclude users matching pattern
        output: Output format
        limit: Maximum results
    """
    # Validate dates
    _validate_dates(from_date, to_date)

    # Get token
    token = _get_token(ctx, app)

    # Get app config
    config = _get_config(ctx)
    app_config = config.get_application(app)

    if not app_config:
        raise EPMValidationError(
            f"Application '{app}' not found in configuration",
            suggestion="Check config/applications.yaml for valid app IDs",
        )

    # Create client
    base_url = app_config.get("url", "")
    client = BaseAPIClient(base_url, token, app)

    console.print(f"[cyan]Querying artifact changes for {app}...[/cyan]")

    # Build query parameters
    params = {
        "startDate": from_date,
        "endDate": to_date,
    }

    if artifact_types:
        params["artifactTypes"] = ",".join(artifact_types)

    if modified_by:
        params["modifiedBy"] = modified_by

    # Make API call
    try:
        results = client._paginated_request(
            "/interop/rest/v1/applications/{app}/artifact-modification",
            params=params,
            limit=limit,
        )

        # Filter out excluded users
        if modified_by_exclude:
            results = [
                r for r in results
                if modified_by_exclude not in r.get("modifiedBy", "")
            ]

        # Classify changes
        for result in results:
            result["classification"] = _classify_change(result)

        # Format output
        if output == "table":
            _print_table(results, output)
        else:
            console.print(format_output(results, output))

        console.print(f"\n[green]✓[/green] Found {len(results)} changes")

    except Exception as e:
        raise EPMValidationError(
            f"Failed to query artifact changes: {str(e)}",
            suggestion="Check application ID and date range",
        )


def _validate_dates(from_date: str, to_date: str) -> None:
    """Validate date format."""
    try:
        datetime.strptime(from_date, "%Y-%m-%d")
        datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
        raise EPMValidationError(
            f"Invalid date format. Use YYYY-MM-DD",
            suggestion="Example: --from 2026-03-01 --to 2026-03-27",
        )


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


def _classify_change(artifact: dict) -> str:
    """Classify artifact change as MATERIAL or OPERATIONAL."""
    artifact_type = artifact.get("artifactType", "").upper()

    if artifact_type in OPERATIONAL_TYPES:
        return "OPERATIONAL"
    elif artifact_type in MATERIAL_TYPES:
        return "MATERIAL"
    else:
        return "REVIEW_REQUIRED"


def _print_table(results: List[dict], output: str) -> None:
    """Print results as table."""
    from rich.table import Table
    from rich.console import Console

    console = Console()
    table = Table(title="Artifact Changes")
    table.add_column("Date", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Modified By", style="yellow")
    table.add_column("Classification", style="magenta")

    for r in results[:50]:  # Limit table display
        date = r.get("modifiedDate", r.get("date", "N/A"))
        if len(date) > 10:
            date = date[:10]  # Just date part
        table.add_row(
            date,
            r.get("artifactType", "N/A"),
            r.get("artifactName", r.get("name", "N/A"))[:30],
            r.get("modifiedBy", "N/A")[:20],
            r.get("classification", "N/A"),
        )

    console.print(table)