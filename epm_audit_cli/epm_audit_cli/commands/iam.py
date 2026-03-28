"""
IAM commands for EPM Audit CLI.

Query OCI IAM for users, groups, and access reviews.
"""

from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table

from epm_audit_cli.exceptions import EPMValidationError
from epm_audit_cli.output import format_output

console = Console()


def _check_oci_available() -> bool:
    """Check if OCI SDK is available."""
    try:
        import oci
        return True
    except ImportError:
        console.print("[red]Error:[/red] OCI SDK not installed")
        console.print("Install with: [cyan]pip install oci[/cyan]")
        return False


@click.group(name="iam")
@click.pass_context
def iam_group(ctx: click.Context) -> None:
    """
    OCI IAM / IDCS identity commands.
    
    Query users, groups, and memberships for SOX access reviews.
    """
    if not _check_oci_available():
        raise SystemExit(1)


@iam_group.command(name="users")
@click.option(
    "--compartment", "-c",
    required=True,
    help="Compartment OCID",
)
@click.option(
    "--filter", "-f",
    type=click.Choice(["all", "service-accounts", "dormant", "privileged", "orphan"]),
    default="all",
    help="Filter users by type",
)
@click.option(
    "--output", "-o",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.option(
    "--file",
    type=click.Path(),
    help="Output file (for CSV format)",
)
@click.pass_context
def iam_users(
    ctx: click.Context,
    compartment: str,
    filter: str,
    output: str,
    file: Optional[str],
) -> None:
    """
    List all users in compartment.
    
    Examples:
        epm iam users --compartment ocid1.compartment.xxx
        epm iam users -c ocid1.compartment.xxx --filter service-accounts
        epm iam users -c ocid1.compartment.xxx --output csv --file users.csv
    """
    from epm_audit_cli.clients.iam import IAMClient
    
    try:
        client = IAMClient()
        users = client.list_users(compartment)
        
        # Apply filter
        if filter == "service-accounts":
            users = [u for u in users if u.get('is_service_account')]
            console.print(f"[cyan]Filtered to {len(users)} service accounts[/cyan]")
        elif filter == "dormant":
            users = [u for u in users if u.get('dormant_days') and u['dormant_days'] > 90]
            console.print(f"[cyan]Filtered to {len(users)} dormant accounts[/cyan]")
        elif filter == "privileged":
            # Get memberships to determine privileged
            memberships = client.get_group_memberships(compartment)
            privileged_ids = set()
            for group_name, user_ids in memberships.items():
                if client._is_privileged_group(group_name):
                    privileged_ids.update(user_ids)
            users = [u for u in users if u['id'] in privileged_ids]
            console.print(f"[cyan]Filtered to {len(users)} privileged users[/cyan]")
        elif filter == "orphan":
            memberships = client.get_group_memberships(compartment)
            all_member_ids = set()
            for user_ids in memberships.values():
                all_member_ids.update(user_ids)
            users = [u for u in users if u['id'] not in all_member_ids]
            console.print(f"[cyan]Filtered to {len(users)} orphan accounts[/cyan]")
        
        if output == "table":
            _print_users_table(users)
        elif output == "json":
            console.print_json(data=users)
        elif output == "csv":
            csv_output = format_output(users, "csv")
            if file:
                with open(file, 'w') as f:
                    f.write(csv_output)
                console.print(f"[green]✓[/green] Wrote {len(users)} users to {file}")
            else:
                console.print(csv_output)
        
        console.print(f"\n[green]✓[/green] Found {len(users)} users")
        
    except Exception as e:
        raise EPMValidationError(
            f"Failed to list users: {str(e)}",
            suggestion="Check compartment OCID and OCI config (~/.oci/config)",
        )


@iam_group.command(name="groups")
@click.option(
    "--compartment", "-c",
    required=True,
    help="Compartment OCID",
)
@click.option(
    "--filter", "-f",
    type=click.Choice(["all", "privileged"]),
    default="all",
    help="Filter groups by type",
)
@click.option(
    "--output", "-o",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.pass_context
def iam_groups(
    ctx: click.Context,
    compartment: str,
    filter: str,
    output: str,
) -> None:
    """
    List all groups in compartment.
    
    Examples:
        epm iam groups --compartment ocid1.compartment.xxx
        epm iam groups -c ocid1.compartment.xxx --filter privileged
    """
    from epm_audit_cli.clients.iam import IAMClient
    
    try:
        client = IAMClient()
        groups = client.list_groups(compartment)
        
        # Apply filter
        if filter == "privileged":
            groups = [g for g in groups if g.get('is_privileged')]
            console.print(f"[cyan]Filtered to {len(groups)} privileged groups[/cyan]")
        
        if output == "table":
            _print_groups_table(groups)
        elif output == "json":
            console.print_json(data=groups)
        elif output == "csv":
            console.print(format_output(groups, "csv"))
        
        console.print(f"\n[green]✓[/green] Found {len(groups)} groups")
        
    except Exception as e:
        raise EPMValidationError(
            f"Failed to list groups: {str(e)}",
            suggestion="Check compartment OCID and OCI config (~/.oci/config)",
        )


@iam_group.command(name="memberships")
@click.option(
    "--compartment", "-c",
    required=True,
    help="Compartment OCID",
)
@click.option(
    "--group", "-g",
    help="Filter by group name",
)
@click.option(
    "--output", "-o",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.pass_context
def iam_memberships(
    ctx: click.Context,
    compartment: str,
    group: Optional[str],
    output: str,
) -> None:
    """
    List user-group memberships.
    
    Examples:
        epm iam memberships --compartment ocid1.compartment.xxx
        epm iam memberships -c ocid1.compartment.xxx --group Administrators
    """
    from epm_audit_cli.clients.iam import IAMClient
    
    try:
        client = IAMClient()
        memberships = client.get_group_memberships(compartment)
        
        # Get user names for display
        users = {u['id']: u['name'] for u in client.list_users(compartment)}
        
        # Apply filter
        if group:
            if group in memberships:
                memberships = {group: memberships[group]}
            else:
                console.print(f"[yellow]Group '{group}' not found[/yellow]")
                memberships = {}
        
        if output == "table":
            _print_memberships_table(memberships, users)
        elif output == "json":
            console.print_json(data=memberships)
        elif output == "csv":
            # Flatten for CSV
            rows = []
            for group_name, user_ids in memberships.items():
                for user_id in user_ids:
                    rows.append({
                        'group': group_name,
                        'user_id': user_id,
                        'user_name': users.get(user_id, 'N/A'),
                    })
            console.print(format_output(rows, "csv"))
        
        total_memberships = sum(len(ids) for ids in memberships.values())
        console.print(f"\n[green]✓[/green] Found {len(memberships)} groups, {total_memberships} memberships")
        
    except Exception as e:
        raise EPMValidationError(
            f"Failed to get memberships: {str(e)}",
            suggestion="Check compartment OCID and OCI config (~/.oci/config)",
        )


@iam_group.command(name="access-review")
@click.option(
    "--compartment", "-c",
    required=True,
    help="Compartment OCID",
)
@click.option(
    "--output", "-o",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.option(
    "--file",
    type=click.Path(),
    help="Output file (for CSV format)",
)
@click.option(
    "--dormant-days",
    type=int,
    default=90,
    help="Days without login to consider dormant (default: 90)",
)
@click.pass_context
def iam_access_review(
    ctx: click.Context,
    compartment: str,
    output: str,
    file: Optional[str],
    dormant_days: int,
) -> None:
    """
    Generate comprehensive SOX access review.
    
    Includes users, groups, memberships, privileged users,
    dormant accounts, orphan accounts, and SoD violations.
    
    Examples:
        epm iam access-review --compartment ocid1.compartment.xxx
        epm iam access-review -c ocid1.compartment.xxx --output csv --file review.csv
    """
    from epm_audit_cli.clients.iam import IAMClient
    
    console.print("[cyan]Generating access review...[/cyan]")
    
    try:
        client = IAMClient()
        review = client.get_access_review(compartment)
        
        if output == "table":
            _print_access_review_summary(review)
        elif output == "json":
            console.print_json(data=review)
        elif output == "csv":
            csv_output = _format_access_review_csv(review)
            if file:
                with open(file, 'w') as f:
                    f.write(csv_output)
                console.print(f"[green]✓[/green] Wrote access review to {file}")
            else:
                console.print(csv_output)
        
    except Exception as e:
        raise EPMValidationError(
            f"Failed to generate access review: {str(e)}",
            suggestion="Check compartment OCID and OCI config (~/.oci/config)",
        )


def _print_users_table(users: List[dict]) -> None:
    """Print users as Rich table."""
    table = Table(title="OCI IAM Users")
    table.add_column("Name", style="cyan")
    table.add_column("Email", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Status", style="dim")
    table.add_column("Created", style="dim")
    
    for user in users[:50]:  # Limit display
        user_type = "Service" if user.get('is_service_account') else "Human"
        status = user.get('lifecycle_state', 'N/A')
        created = user.get('time_created', 'N/A')
        if created and len(created) > 10:
            created = created[:10]
        
        table.add_row(
            user.get('name', 'N/A')[:30],
            user.get('email', 'N/A')[:30],
            user_type,
            status,
            created,
        )
    
    console.print(table)
    if len(users) > 50:
        console.print(f"[dim]Showing 50 of {len(users)} users[/dim]")


def _print_groups_table(groups: List[dict]) -> None:
    """Print groups as Rich table."""
    table = Table(title="OCI IAM Groups")
    table.add_column("Name", style="cyan")
    table.add_column("Members", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Status", style="dim")
    
    for group in groups:
        group_type = "Privileged" if group.get('is_privileged') else "Standard"
        member_count = group.get('member_count', 'N/A')
        status = group.get('lifecycle_state', 'N/A')
        
        table.add_row(
            group.get('name', 'N/A')[:30],
            str(member_count),
            group_type,
            status,
        )
    
    console.print(table)


def _print_memberships_table(memberships: dict, users: dict) -> None:
    """Print memberships as Rich table."""
    table = Table(title="Group Memberships")
    table.add_column("Group", style="cyan")
    table.add_column("Member Count", style="green")
    table.add_column("Members (first 5)", style="dim")
    
    for group_name, user_ids in sorted(memberships.items()):
        member_names = [users.get(uid, uid[:20]) for uid in user_ids[:5]]
        members_str = ", ".join(member_names)
        if len(user_ids) > 5:
            members_str += f" ... (+{len(user_ids) - 5})"
        
        table.add_row(
            group_name[:30],
            str(len(user_ids)),
            members_str[:50],
        )
    
    console.print(table)


def _print_access_review_summary(review: dict) -> None:
    """Print access review summary."""
    summary = review.get('summary', {})
    
    # Summary table
    table = Table(title="Access Review Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Count", style="green")
    
    table.add_row("Total Users", str(summary.get('total_users', 0)))
    table.add_row("Human Users", str(summary.get('human_users', 0)))
    table.add_row("Service Accounts", str(summary.get('service_accounts', 0)))
    table.add_row("Privileged Users", str(summary.get('privileged_users', 0)))
    table.add_row("Dormant Accounts", str(summary.get('dormant_accounts', 0)))
    table.add_row("Orphan Accounts", str(summary.get('orphan_accounts', 0)))
    table.add_row("Total Groups", str(summary.get('total_groups', 0)))
    table.add_row("Privileged Groups", str(summary.get('privileged_groups', 0)))
    table.add_row("SoD Violations", str(summary.get('sod_violations', 0)))
    
    console.print(table)
    
    # Security flags
    flags = review.get('security_flags', [])
    if flags:
        console.print("\n[bold red]Security Flags:[/bold red]")
        for flag in flags:
            severity = flag.get('severity', 'UNKNOWN')
            color = 'red' if severity == 'HIGH' else 'yellow' if severity == 'MEDIUM' else 'dim'
            console.print(f"  [{color}]{severity}[/{color}] {flag.get('type')}: {flag.get('message')}")
            console.print(f"    [dim]Remediation: {flag.get('remediation')}[/dim]")
    
    # Recommendations
    recommendations = review.get('recommendations', [])
    if recommendations:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in recommendations:
            console.print(f"  • {rec}")


def _format_access_review_csv(review: dict) -> str:
    """Format access review as CSV."""
    import csv
    import io
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Summary section
    writer.writerow(["# Access Review Summary"])
    summary = review.get('summary', {})
    for key, value in summary.items():
        writer.writerow([key, value])
    
    writer.writerow([])
    
    # Users section
    writer.writerow(["# Users"])
    writer.writerow(["Name", "Email", "Type", "Status", "Dormant Days"])
    for user in review.get('users', []):
        writer.writerow([
            user.get('name', ''),
            user.get('email', ''),
            'Service' if user.get('is_service_account') else 'Human',
            user.get('lifecycle_state', ''),
            user.get('dormant_days', ''),
        ])
    
    writer.writerow([])
    
    # Groups section
    writer.writerow(["# Groups"])
    writer.writerow(["Name", "Member Count", "Type", "Status"])
    for group in review.get('groups', []):
        writer.writerow([
            group.get('name', ''),
            group.get('member_count', ''),
            'Privileged' if group.get('is_privileged') else 'Standard',
            group.get('lifecycle_state', ''),
        ])
    
    writer.writerow([])
    
    # Security flags
    writer.writerow(["# Security Flags"])
    writer.writerow(["Severity", "Type", "Message", "Remediation"])
    for flag in review.get('security_flags', []):
        writer.writerow([
            flag.get('severity', ''),
            flag.get('type', ''),
            flag.get('message', ''),
            flag.get('remediation', ''),
        ])
    
    return output.getvalue()