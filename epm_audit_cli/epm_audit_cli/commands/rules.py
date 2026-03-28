"""
Business rules commands for EPM Audit CLI.

List, get, and diff business rules.
"""

from typing import Optional
import click
from rich.console import Console
from rich.table import Table
import json
from pathlib import Path

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


def rules(
    ctx: click.Context,
    app: str,
    rule_type: str,
    output: str,
    limit: int,
) -> None:
    """List business rules for an application."""
    token = _get_token(ctx, app)
    config = _get_config(ctx)
    app_config = config.get_application(app)

    if not app_config:
        raise EPMValidationError(f"Application '{app}' not found", suggestion="Check config/applications.yaml")

    base_url = app_config.get("url", "")
    client = BaseAPIClient(base_url, token, app)

    console.print(f"[cyan]Listing business rules for {app}...[/cyan]")

    params = {}
    if rule_type != "ALL":
        params["ruleType"] = rule_type

    try:
        results = client._paginated_request(
            "/HyperionPlanning/rest/v3/applications/{app}/calculations",
            params=params,
            limit=limit,
        )

        if output == "table":
            table = Table(title="Business Rules")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Last Modified", style="dim")
            table.add_column("Modified By", style="yellow")

            for r in results[:50]:
                table.add_row(
                    r.get("name", r.get("calcName", "N/A"))[:40],
                    r.get("ruleType", "CALCULATION"),
                    r.get("lastModified", "N/A")[:10],
                    r.get("modifiedBy", "N/A")[:20],
                )
            console.print(table)
        else:
            console.print(format_output(results, output))

        console.print(f"\n[green]✓[/green] Found {len(results)} rules")

    except Exception as e:
        raise EPMValidationError(
            f"Failed to list rules: {str(e)}",
            suggestion="Check application ID and try again",
        )


def rule(
    ctx: click.Context,
    app: str,
    rule_id: str,
    output_file: Optional[str],
) -> None:
    """Get business rule definition."""
    token = _get_token(ctx, app)
    config = _get_config(ctx)
    app_config = config.get_application(app)

    if not app_config:
        raise EPMValidationError(f"Application '{app}' not found", suggestion="Check config/applications.yaml")

    base_url = app_config.get("url", "")
    client = BaseAPIClient(base_url, token, app)

    console.print(f"[cyan]Getting rule {rule_id}...[/cyan]")

    try:
        result = client.get(
            f"/HyperionPlanning/rest/v3/applications/{app}/calculations/{rule_id}"
        )

        # Display result
        console.print(format_output(result, "json"))

        if output_file:
            # Save to file
            output_path = Path(output_file)
            output_path.write_text(json.dumps(result, indent=2))
            console.print(f"[green]✓[/green] Saved to {output_file}")

    except Exception as e:
        raise EPMValidationError(
            f"Failed to get rule: {str(e)}",
            suggestion="Check rule ID and try 'epm rules' to list available rules",
        )


def rule_diff(
    ctx: click.Context,
    app: str,
    rule_id: str,
    baseline: str,
) -> None:
    """Compare current rule against baseline."""
    token = _get_token(ctx, app)
    config = _get_config(ctx)
    app_config = config.get_application(app)

    if not app_config:
        raise EPMValidationError(f"Application '{app}' not found", suggestion="Check config/applications.yaml")

    base_url = app_config.get("url", "")
    client = BaseAPIClient(base_url, token, app)

    # Load baseline
    baseline_path = Path(baseline)
    if not baseline_path.exists():
        raise EPMValidationError(
            f"Baseline file not found: {baseline}",
            suggestion="Provide a valid path to a JSON baseline file",
        )

    baseline_data = json.loads(baseline_path.read_text())

    console.print(f"[cyan]Comparing rule {rule_id} against baseline...[/cyan]")

    try:
        # Get current rule
        current = client.get(
            f"/HyperionPlanning/rest/v3/applications/{app}/calculations/{rule_id}"
        )

        # Compare
        differences = _compare_rules(baseline_data, current)

        if not differences:
            console.print("[green]✓[/green] No differences found")
            return

        # Display differences
        table = Table(title="Differences")
        table.add_column("Field", style="cyan")
        table.add_column("Baseline", style="dim")
        table.add_column("Current", style="yellow")

        for diff in differences:
            table.add_row(
                diff["field"],
                str(diff["baseline"])[:40],
                str(diff["current"])[:40],
            )

        console.print(table)
        console.print(f"\n[yellow]Found {len(differences)} differences[/yellow]")

    except Exception as e:
        raise EPMValidationError(
            f"Failed to compare rule: {str(e)}",
            suggestion="Check rule ID and baseline file",
        )


def _compare_rules(baseline: dict, current: dict) -> list:
    """Compare two rule definitions and return differences."""
    differences = []

    # Compare key fields
    fields_to_compare = [
        "formula",
        "script",
        "memberScope",
        "executionOrder",
        "runTimePromptValues",
        "lastModified",
        "modifiedBy",
    ]

    for field in fields_to_compare:
        baseline_val = baseline.get(field)
        current_val = current.get(field)

        if baseline_val != current_val:
            differences.append({
                "field": field,
                "baseline": baseline_val,
                "current": current_val,
            })

    return differences