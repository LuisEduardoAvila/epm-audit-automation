"""
Config command for EPM Audit CLI.

Provides commands for managing configuration including:
- config init: Initialize a new configuration file from template
"""

import os
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()


@click.group(name="config")
@click.pass_context
def config_group(ctx: click.Context) -> None:
    """Manage EPM CLI configuration.
    
    Commands for initializing and managing the applications.yaml config file.
    
    Examples:
        epm config init
        epm config init --interactive
        epm config init --output /path/to/config.yaml
    """
    pass


@config_group.command(name="init")
@click.option(
    "--output", "-o",
    type=click.Path(),
    default=None,
    help="Output path for the config file (default: config/applications.yaml)",
)
@click.option(
    "--interactive", "-i",
    is_flag=True,
    help="Interactive mode: prompt for configuration values",
)
@click.option(
    "--force", "-f",
    is_flag=True,
    help="Overwrite existing config file",
)
def config_init(output: Optional[str], interactive: bool, force: bool) -> None:
    """Initialize a new configuration file from template.
    
    Creates a configuration file based on the template with placeholder values.
    Use --interactive to be prompted for specific values.
    
    Examples:
        epm config init
        epm config init --interactive
        epm config init --output ~/my-epm-config.yaml --force
    """
    # Determine output path
    if output:
        config_path = Path(output)
    else:
        # Default to config/applications.yaml in current directory
        config_path = Path("config/applications.yaml")

    # Check if file exists
    if config_path.exists() and not force:
        if not Confirm.ask(
            f"[yellow]File {config_path} already exists. Overwrite?[/yellow]"
        ):
            console.print("[cyan]Config initialization cancelled.[/cyan]")
            return

    # Create parent directories if needed
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if interactive:
        _create_interactive_config(config_path)
    else:
        _create_template_config(config_path)


def _create_template_config(config_path: Path) -> None:
    """Create config from template file."""
    # Get the template path
    template_path = Path(__file__).parent.parent / "templates" / "config_template.yaml"

    if not template_path.exists():
        raise click.ClickException(
            f"Template file not found: {template_path}"
        )

    # Read template and write to output
    template_content = template_path.read_text()
    config_path.write_text(template_content)

    console.print(f"[green]✓[/green] Configuration file created: {config_path}")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print("  1. Edit the configuration file and update placeholder values")
    console.print("  2. Run 'epm login <app_id>' to authenticate")
    console.print("  3. Run 'epm artifact-changes --app <app_id> --from DATE --to DATE' to query changes")


def _create_interactive_config(config_path: Path) -> None:
    """Create config interactively by prompting for values."""
    
    console.print("\n[bold cyan]EPM Audit CLI Configuration[/bold cyan]")
    console.print("Enter your EPM Cloud application details:\n")

    # Collect application details
    app_id = Prompt.ask(
        "[cyan]Application ID[/cyan]",
        default="fccs_prod",
    )

    app_type = Prompt.ask(
        "[cyan]Application type[/cyan]",
        default="fccs",
        choices=["fcs", "fccs", "edm", "planning", "pbcs"],
    )

    app_name = Prompt.ask(
        "[cyan]Application name[/cyan]",
        default="My EPM Application",
    )

    # Get URL - need to prompt for each part
    pod_name = Prompt.ask(
        "[cyan]POD name (e.g., epmadm01)[/cyan]",
        default="epmadm01",
    )

    # Determine base URL based on type
    if app_type in ["fcs", "fccs"]:
        base_url = f"https://{pod_name}.epm.usphoenix1.oraclevcn.com"
    elif app_type == "edm":
        base_url = f"https://{pod_name}.edm.usphoenix1.oraclevcn.com"
    elif app_type in ["planning", "pbcs"]:
        base_url = f"https://{pod_name}.pbcs.usphoenix1.oraclevcn.com"
    else:
        base_url = f"https://{pod_name}.epm.usphoenix1.oraclevcn.com"

    environment = Prompt.ask(
        "[cyan]Environment[/cyan]",
        default="prod",
        choices=["prod", "test", "dev"],
    )

    # Optional: compartment OCID for IAM commands
    add_oci = Confirm.ask(
        "[cyan]Configure OCI IAM settings?[/cyan]",
        default=False,
    )

    compartment_ocid = None
    if add_oci:
        compartment_ocid = Prompt.ask(
            "[cyan]Compartment OCID[/cyan]",
            default="",
        )

    # Generate config content
    config_content = _generate_config_content(
        app_id=app_id,
        app_type=app_type,
        app_name=app_name,
        base_url=base_url,
        environment=environment,
        pod_name=pod_name,
        compartment_ocid=compartment_ocid if compartment_ocid else None,
    )

    # Write config
    config_path.write_text(config_content)

    console.print(f"\n[green]✓[/green] Configuration file created: {config_path}")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print(f"  1. Review the configuration at {config_path}")
    console.print("  2. Run 'epm login {app_id}' to authenticate")


def _generate_config_content(
    app_id: str,
    app_type: str,
    app_name: str,
    base_url: str,
    environment: str,
    pod_name: str,
    compartment_ocid: Optional[str] = None,
) -> str:
    """Generate configuration content from provided values."""
    
    content = f"""# EPM Audit CLI Configuration
# Generated by 'epm config init --interactive'
# 
# This file configures EPM Cloud applications for audit operations.
# Update the values below to match your EPM environment.

# Default settings applied to all applications
defaults:
  # Default output format (table, json, csv)
  output_format: table
  # Default timeout for API requests (seconds)
  timeout: 30
  # Enable verbose logging
  verbose: false
  # Default number of results to return
  default_limit: 50

# Application definitions
applications:
  {app_id}:
    # Application type: fccs, edm, planning, pbcs
    type: {app_type}
    # Descriptive name
    name: "{app_name}"
    # EPM Cloud base URL
    url: "{base_url}"
    # Identity domain / POD identifier
    identity_domain: "{pod_name}"
    # Environment: prod, test, dev
    environment: {environment}
"""

    if compartment_ocid:
        content += f"""    # Optional: OCI compartment OCID for IAM commands
    compartment_ocid: "{compartment_ocid}"
"""

    content += """
# Optional: OCI configuration for infrastructure commands
# oci:
#   # Default compartment OCID (used if not specified in command)
#   compartment_ocid: "ocid1.compartment.xxx"
#   # OCI region
#   region: "us-phoenix-1"
#   # Tenancy OCID
#   tenancy_ocid: "ocid1.tenancy.xxx"

# Optional: Credential settings
# credentials:
#   # Backend for storing credentials: oci_vault, keyring
#   backend: oci_vault

# Optional: Token settings
# tokens:
#   # Backend for storing tokens: keyring, file, env
#   backend: keyring
#   # Token expiration (hours)
#   expiration_hours: 24
"""

    return content


@config_group.command(name="validate")
@click.argument("config_file", type=click.Path(exists=True), default=None)
def config_validate(config_file: Optional[str]) -> None:
    """Validate a configuration file.
    
    Checks that the configuration file is valid and all applications
    have the required fields.
    
    Examples:
        epm config validate
        epm config validate /path/to/config.yaml
    """
    from epm_audit_cli.config.loader import ConfigLoader
    from epm_audit_cli.exceptions import EPMConfigurationError

    # Determine config path
    if config_file:
        config_path = Path(config_file)
    else:
        config_path = Path("config/applications.yaml")

    if not config_path.exists():
        raise click.ClickException(
            f"Configuration file not found: {config_path}"
        )

    try:
        config = ConfigLoader(str(config_path))
        apps = config.list_applications()

        if not apps:
            console.print("[yellow]Warning: No applications configured[/yellow]")
            return

        console.print(f"[green]✓[/green] Configuration is valid")
        console.print(f"  Found {len(apps)} application(s):")

        for app_id, app_config in apps.items():
            app_type = app_config.get("type", "unknown")
            url = app_config.get("url", "N/A")
            console.print(f"  - {app_id}: {app_type} ({url})")

    except EPMConfigurationError as e:
        raise click.ClickException(f"Configuration error: {e}")
    except Exception as e:
        raise click.ClickException(f"Failed to load configuration: {e}")


@config_group.command(name="list")
def config_list() -> None:
    """List configured applications.
    
    Displays all applications defined in the configuration file.
    
    Examples:
        epm config list
    """
    from epm_audit_cli.config.loader import ConfigLoader
    from rich.table import Table

    # Try to load config
    config_path = Path("config/applications.yaml")

    if not config_path.exists():
        console.print("[yellow]No configuration file found[/yellow]")
        console.print("Run 'epm config init' to create one")
        return

    try:
        config = ConfigLoader(str(config_path))
        apps = config.list_applications()

        if not apps:
            console.print("[yellow]No applications configured[/yellow]")
            return

        table = Table(title="Configured Applications")
        table.add_column("App ID", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Name", style="blue")
        table.add_column("URL", style="dim")

        for app_id, app_config in apps.items():
            app_type = app_config.get("type", "unknown")
            app_name = app_config.get("name", "N/A")
            url = app_config.get("url", "N/A")
            # Truncate URL for display
            if len(url) > 40:
                url = url[:37] + "..."
            table.add_row(app_id, app_type, app_name, url)

        console.print(table)

    except Exception as e:
        raise click.ClickException(f"Failed to load configuration: {e}")


# Export for CLI registration
__all__ = ["config_group"]