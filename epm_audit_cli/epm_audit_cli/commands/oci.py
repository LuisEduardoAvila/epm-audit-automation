"""
OCI infrastructure commands for EPM Audit CLI.

Monitor OCI compute, storage, and networking.
"""

from typing import Optional
import click
from rich.console import Console
from rich.table import Table

from epm_audit_cli.config.loader import ConfigLoader
from epm_audit_cli.exceptions import EPMValidationError

console = Console()


def _check_oci_available() -> bool:
    """Check if OCI SDK is available."""
    try:
        import oci
        return True
    except ImportError:
        return False


def oci_instances(
    ctx: click.Context,
    compartment: str,
    filter_tag: Optional[str],
    status: str,
    output: str,
) -> None:
    """List OCI compute instances."""
    if not _check_oci_available():
        console.print("[red]Error:[/red] OCI SDK not installed")
        console.print("Install with: pip install oci")
        return

    from oci import config as oci_config
    from oci.core import ComputeClient, ComputeClientCompositeOperations
    from oci.core.models import Instance

    console.print(f"[cyan]Querying OCI instances in compartment {compartment[:20]}...[/cyan]")

    try:
        # Load OCI config
        config = oci_config.from_file()

        # Create compute client
        compute = ComputeClient(config)

        # List instances
        instances = compute.list_instances(compartment_id=compartment).data

        # Filter by status
        if status != "ALL":
            instances = [i for i in instances if i.lifecycle_state == status]

        # Filter by tag
        if filter_tag:
            key, value = filter_tag.split("=", 1)
            instances = [
                i for i in instances
                if i.freeform_tags and i.freeform_tags.get(key) == value
            ]

        if output == "table":
            table = Table(title="OCI Compute Instances")
            table.add_column("Name", style="cyan")
            table.add_column("Shape", style="green")
            table.add_column("State", style="yellow")
            table.add_column("Created", style="dim")

            for inst in instances[:50]:
                table.add_row(
                    inst.display_name[:30],
                    inst.shape,
                    inst.lifecycle_state,
                    inst.time_created.strftime("%Y-%m-%d") if inst.time_created else "N/A",
                )
            console.print(table)
        else:
            # Convert to dict for JSON/CSV output
            data = [{
                "name": i.display_name,
                "shape": i.shape,
                "state": i.lifecycle_state,
                "created": str(i.time_created) if i.time_created else None,
                "id": i.id,
            } for i in instances]

            from epm_audit_cli.output import format_output
            console.print(format_output(data, output))

        console.print(f"\n[green]✓[/green] Found {len(instances)} instances")

    except Exception as e:
        raise EPMValidationError(
            f"Failed to query OCI instances: {str(e)}",
            suggestion="Check OCI config file (~/.oci/config) and compartment OCID",
        )


def oci_storage(
    ctx: click.Context,
    bucket: str,
    compartment: Optional[str],
    output: str,
) -> None:
    """Get OCI storage bucket information."""
    if not _check_oci_available():
        console.print("[red]Error:[/red] OCI SDK not installed")
        console.print("Install with: pip install oci")
        return

    from oci import config as oci_config
    from oci.object_storage import ObjectStorageClient

    console.print(f"[cyan]Querying OCI storage bucket {bucket}...[/cyan]")

    try:
        # Load OCI config
        config = oci_config.from_file()

        # Create object storage client
        client = ObjectStorageClient(config)
        namespace = client.get_namespace().data

        # Get bucket info
        bucket_info = client.get_bucket(namespace_name=namespace, bucket_name=bucket).data

        # List objects
        objects = client.list_objects(namespace_name=namespace, bucket_name=bucket).data

        if output == "table":
            table = Table(title=f"OCI Bucket: {bucket}")
            table.add_column("Name", style="cyan")
            table.add_column("Size", style="green")
            table.add_column("Modified", style="dim")

            total_size = 0
            for obj in objects.objects[:50]:
                size = obj.size or 0
                total_size += size
                table.add_row(
                    obj.name[:40],
                    f"{size / 1024 / 1024:.2f} MB",
                    obj.time_modified.strftime("%Y-%m-%d") if obj.time_modified else "N/A",
                )

            console.print(table)
            console.print(f"\nTotal objects: {len(objects.objects)}")
            console.print(f"Total size: {total_size / 1024 / 1024 / 1024:.2f} GB")
        else:
            data = {
                "bucket": bucket,
                "namespace": namespace,
                "object_count": len(objects.objects),
                "total_size_bytes": sum(o.size or 0 for o in objects.objects),
            }

            from epm_audit_cli.output import format_output
            console.print(format_output(data, output))

    except Exception as e:
        raise EPMValidationError(
            f"Failed to query OCI storage: {str(e)}",
            suggestion="Check bucket name and OCI config",
        )


def oci_network(
    ctx: click.Context,
    vcn: str,
    compartment: Optional[str],
    output: str,
) -> None:
    """Get OCI network status."""
    if not _check_oci_available():
        console.print("[red]Error:[/red] OCI SDK not installed")
        console.print("Install with: pip install oci")
        return

    from oci import config as oci_config
    from oci.core import VirtualNetworkClient

    console.print(f"[cyan]Querying OCI VCN {vcn[:20]}...[/cyan]")

    try:
        # Load OCI config
        config = oci_config.from_file()

        # Create VCN client
        client = VirtualNetworkClient(config)

        # Get VCN info
        vcn_info = client.get_vcn(vcn_id=vcn).data

        # Get subnets
        subnets = client.list_subnets(compartment_id=vcn_info.compartment_id, vcn_id=vcn).data

        # Get security lists
        security_lists = client.list_security_lists(
            compartment_id=vcn_info.compartment_id, vcn_id=vcn
        ).data

        if output == "table":
            table = Table(title=f"OCI VCN: {vcn_info.display_name}")
            table.add_column("Resource", style="cyan")
            table.add_column("Name", style="green")
            table.add_column("State", style="yellow")

            table.add_row("VCN", vcn_info.display_name, vcn_info.lifecycle_state)

            for subnet in subnets[:10]:
                table.add_row(
                    "Subnet",
                    subnet.display_name[:30],
                    subnet.lifecycle_state,
                )

            for sec_list in security_lists[:10]:
                table.add_row(
                    "Security List",
                    sec_list.display_name[:30],
                    sec_list.lifecycle_state,
                )

            console.print(table)
        else:
            data = {
                "vcn": {
                    "name": vcn_info.display_name,
                    "id": vcn_info.id,
                    "cidr_block": vcn_info.cidr_block,
                    "state": vcn_info.lifecycle_state,
                },
                "subnets": [
                    {"name": s.display_name, "cidr": s.cidr_block, "state": s.lifecycle_state}
                    for s in subnets
                ],
                "security_lists": [
                    {"name": sl.display_name, "state": sl.lifecycle_state}
                    for sl in security_lists
                ],
            }

            from epm_audit_cli.output import format_output
            console.print(format_output(data, output))

    except Exception as e:
        raise EPMValidationError(
            f"Failed to query OCI network: {str(e)}",
            suggestion="Check VCN OCID and OCI config",
        )