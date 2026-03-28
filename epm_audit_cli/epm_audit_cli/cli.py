"""
EPM Audit CLI - Main entry point

Provides commands for Oracle EPM Cloud audit operations:
- Authentication (login, logout)
- Artifact change tracking
- EDM request history
- Business rule inspection
- OCI infrastructure monitoring
"""

import sys
from typing import Optional

import click
from rich.console import Console

from epm_audit_cli import __version__
from epm_audit_cli.config.loader import ConfigLoader
from epm_audit_cli.output import format_output, get_formatter
from epm_audit_cli.commands.login import login
from epm_audit_cli.commands.logout import logout
from epm_audit_cli.commands.artifact import artifact_changes
from epm_audit_cli.commands.edm import edm_requests, edm_request, edm_violations
from epm_audit_cli.commands.rules import rules, rule, rule_diff
from epm_audit_cli.commands.oci import oci_instances, oci_storage, oci_network

console = Console()


class CLIContext:
    """Shared CLI context"""

    def __init__(self):
        self.config: Optional[ConfigLoader] = None
        self.verbose: bool = False
        self.output_format: str = "table"


@click.group()
@click.version_option(version=__version__)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to applications.yaml config file",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose/debug output",
)
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool) -> None:
    """
    EPM Audit CLI - Oracle EPM audit operations

    Provides commands for SOX compliance and governance workflows including:
    - Artifact change tracking
    - EDM request history
    - Business rule inspection
    - OCI infrastructure monitoring
    """
    # Initialize CLI context
    ctx_obj = ctx.ensure_object(CLIContext)
    ctx_obj.verbose = verbose
    ctx_obj.verbose = verbose

    # Load configuration
    if config:
        ctx_obj.config = ConfigLoader(config)
    else:
        # Try default location
        try:
            default_config = "config/applications.yaml"
            ctx_obj.config = ConfigLoader(default_config)
        except FileNotFoundError:
            if verbose:
                console.print(
                    "[yellow]Warning: No config file specified and "
                    "config/applications.yaml not found[/yellow]"
                )
            ctx_obj.config = None


@cli.command(name="login")
@click.argument("app", required=False)
@click.option(
    "--verify",
    is_flag=True,
    help="Verify connection after login",
)
@click.option(
    "--backend",
    type=click.Choice(["auto", "oci_vault", "keyring", "env"]),
    default="auto",
    help="Credential backend to use",
)
@click.pass_context
def login_cmd(
    ctx: click.Context,
    app: Optional[str],
    verify: bool,
    backend: str,
) -> None:
    """Authenticate to an EPM application.

    APP is the application ID from applications.yaml (e.g., fccs_prod).
    If no APP is specified, lists available applications.

    Examples:
        epm login fccs_prod
        epm login fccs_prod --verify
    """
    login(ctx, app, verify, backend)


@cli.command(name="logout")
@click.option(
    "--all",
    "logout_all",
    is_flag=True,
    help="Logout from all applications",
)
@click.pass_context
def logout_cmd(ctx: click.Context, logout_all: bool) -> None:
    """End authentication session.

    Examples:
        epm logout
        epm logout --all
    """
    logout(ctx, logout_all)


@cli.command(name="artifact-changes")
@click.option(
    "--app",
    required=True,
    help="Application ID from config (e.g., fccs_prod)",
)
@click.option(
    "--from",
    "from_date",
    required=True,
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--to",
    "to_date",
    required=True,
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--type",
    "artifact_types",
    multiple=True,
    help="Filter by artifact type (can be specified multiple times)",
)
@click.option(
    "--modified-by",
    help="Filter by user who modified",
)
@click.option(
    "--modified-by-exclude",
    help="Filter out changes by user pattern (e.g., svc_*)",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.option(
    "--limit",
    type=int,
    default=100,
    help="Maximum number of results",
)
@click.pass_context
def artifact_changes_cmd(
    ctx: click.Context,
    app: str,
    from_date: str,
    to_date: str,
    artifact_types: tuple,
    modified_by: Optional[str],
    modified_by_exclude: Optional[str],
    output: str,
    limit: int,
) -> None:
    """Query artifact modification history.

    Examples:
        epm artifact-changes --app fccs_prod --from 2026-03-01 --to 2026-03-27
        epm artifact-changes --app fccs_prod --from 2026-03-01 --type CONSOLIDATION_RULE --output json
    """
    artifact_changes(
        ctx,
        app,
        from_date,
        to_date,
        list(artifact_types),
        modified_by,
        modified_by_exclude,
        output,
        limit,
    )


@cli.command(name="edm-requests")
@click.option(
    "--app",
    required=True,
    help="EDM application ID",
)
@click.option(
    "--status",
    type=click.Choice(["COMPLETED", "PENDING", "REJECTED", "APPROVED"]),
    help="Filter by request status",
)
@click.option(
    "--from",
    "from_date",
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--to",
    "to_date",
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.option(
    "--limit",
    type=int,
    default=50,
    help="Maximum number of results",
)
@click.pass_context
def edm_requests_cmd(
    ctx: click.Context,
    app: str,
    status: Optional[str],
    from_date: Optional[str],
    to_date: Optional[str],
    output: str,
    limit: int,
) -> None:
    """List EDM request history.

    Examples:
        epm edm-requests --app edm_prod --status COMPLETED
        epm edm-requests --app edm_prod --from 2026-03-01 --output json
    """
    edm_requests(
        ctx, app, status, from_date, to_date, output, limit
    )


@cli.command(name="edm-request")
@click.option(
    "--app",
    required=True,
    help="EDM application ID",
)
@click.option(
    "--id",
    "request_id",
    required=True,
    help="EDM request ID (e.g., REQ-2026-0226-001)",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.pass_context
def edm_request_cmd(
    ctx: click.Context,
    app: str,
    request_id: str,
    output: str,
) -> None:
    """Get EDM request details.

    Examples:
        epm edm-request --app edm_prod --id REQ-2026-0226-001
    """
    edm_request(ctx, app, request_id, output)


@cli.command(name="edm-violations")
@click.option(
    "--app",
    required=True,
    help="EDM application ID",
)
@click.option(
    "--from",
    "from_date",
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--to",
    "to_date",
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--severity",
    type=click.Choice(["CRITICAL", "HIGH", "MEDIUM", "LOW"]),
    help="Filter by severity",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.option(
    "--limit",
    type=int,
    default=50,
    help="Maximum number of results",
)
@click.pass_context
def edm_violations_cmd(
    ctx: click.Context,
    app: str,
    from_date: Optional[str],
    to_date: Optional[str],
    severity: Optional[str],
    output: str,
    limit: int,
) -> None:
    """List EDM policy violations.

    Examples:
        epm edm-violations --app edm_prod
        epm edm-violations --app edm_prod --severity HIGH
    """
    edm_violations(
        ctx, app, from_date, to_date, severity, output, limit
    )


@cli.command(name="rules")
@click.option(
    "--app",
    required=True,
    help="Planning/Budgets application ID",
)
@click.option(
    "--type",
    "rule_type",
    type=click.Choice(["CALCULATION", "MEMBER", "ALL"]),
    default="ALL",
    help="Filter by rule type",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.option(
    "--limit",
    type=int,
    default=50,
    help="Maximum number of results",
)
@click.pass_context
def rules_cmd(
    ctx: click.Context,
    app: str,
    rule_type: str,
    output: str,
    limit: int,
) -> None:
    """List business rules for an application.

    Examples:
        epm rules --app pbcs_prod
        epm rules --app pbcs_prod --type CALCULATION --output json
    """
    rules(ctx, app, rule_type, output, limit)


@cli.command(name="rule")
@click.option(
    "--app",
    required=True,
    help="Planning/Budgets application ID",
)
@click.option(
    "--id",
    "rule_id",
    required=True,
    help="Rule ID/name",
)
@click.option(
    "--output-file",
    type=click.Path(),
    help="Save rule definition to file",
)
@click.pass_context
def rule_cmd(
    ctx: click.Context,
    app: str,
    rule_id: str,
    output_file: Optional[str],
) -> None:
    """Get business rule definition.

    Examples:
        epm rule --app pbcs_prod --id Calc_Headcount
        epm rule --app pbcs_prod --id Calc_Headcount --output-file formula.txt
    """
    rule(ctx, app, rule_id, output_file)


@cli.command(name="rule-diff")
@click.option(
    "--app",
    required=True,
    help="Planning/Budgets application ID",
)
@click.option(
    "--id",
    "rule_id",
    required=True,
    help="Rule ID/name",
)
@click.option(
    "--baseline",
    required=True,
    type=click.Path(exists=True),
    help="Baseline file (JSON) to compare against",
)
@click.pass_context
def rule_diff_cmd(
    ctx: click.Context,
    app: str,
    rule_id: str,
    baseline: str,
) -> None:
    """Compare current rule against baseline.

    Examples:
        epm rule-diff --app pbcs_prod --id Calc_Headcount --baseline snapshot.json
    """
    rule_diff(ctx, app, rule_id, baseline)


@cli.command(name="oci-instances")
@click.option(
    "--compartment",
    required=True,
    help="OCI Compartment OCID",
)
@click.option(
    "--filter-tag",
    help="Filter by tag (e.g., epm=true)",
)
@click.option(
    "--status",
    type=click.Choice(["RUNNING", "STOPPED", "ALL"]),
    default="ALL",
    help="Filter by instance status",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.pass_context
def oci_instances_cmd(
    ctx: click.Context,
    compartment: str,
    filter_tag: Optional[str],
    status: str,
    output: str,
) -> None:
    """List OCI compute instances.

    Examples:
        epm oci-instances --compartment ocid1.compartment.xxx
    """
    oci_instances(ctx, compartment, filter_tag, status, output)


@cli.command(name="oci-storage")
@click.option(
    "--bucket",
    required=True,
    help="OCI Object Storage bucket name",
)
@click.option(
    "--compartment",
    help="Compartment OCID (if different from default)",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.pass_context
def oci_storage_cmd(
    ctx: click.Context,
    bucket: str,
    compartment: Optional[str],
    output: str,
) -> None:
    """Get OCI storage bucket information.

    Examples:
        epm oci-storage --bucket epm-backups
    """
    oci_storage(ctx, bucket, compartment, output)


@cli.command(name="oci-network")
@click.option(
    "--vcn",
    required=True,
    help="OCI VCN OCID",
)
@click.option(
    "--compartment",
    help="Compartment OCID (if different from default)",
)
@click.option(
    "--output",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.pass_context
def oci_network_cmd(
    ctx: click.Context,
    vcn: str,
    compartment: Optional[str],
    output: str,
) -> None:
    """Get OCI network status.

    Examples:
        epm oci-network --vcn ocid1.vcn.xxx
    """
    oci_network(ctx, vcn, compartment, output)


def main() -> None:
    """Main entry point"""
    cli(obj=None)


if __name__ == "__main__":
    main()