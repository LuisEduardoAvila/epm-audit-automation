"""
Table output formatter using Rich.

Provides human-readable table output for CLI commands.
"""

from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.table import Table

console = Console()


def format_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
    max_rows: int = 50,
) -> str:
    """
    Format data as a Rich table.

    Args:
        data: List of dictionaries (rows)
        columns: Column names to include (None = all keys)
        title: Table title
        max_rows: Maximum rows to display

    Returns:
        Formatted table string
    """
    if not data:
        return "No data to display"

    # Get columns from first row if not specified
    if columns is None:
        # Use first row keys, but order sensibly
        first_row = data[0]
        columns = list(first_row.keys())

    # Truncate data if needed
    display_data = data[:max_rows]
    truncated = len(data) > max_rows

    # Create table
    table = Table(
        show_header=True,
        header_style="bold cyan",
        title=title,
        title_style="bold green",
    )

    # Add columns
    for col in columns:
        table.add_column(col, no_wrap=False)

    # Add rows
    for row in display_data:
        table.add_row(*[_format_cell(row.get(col, "")) for col in columns])

    # Render to string
    output = table
    if truncated:
        output = f"{output}\n[yellow]... and {len(data) - max_rows} more rows[/yellow]"

    return str(output)


def _format_cell(value: Any) -> str:
    """Format a cell value for display"""
    if value is None:
        return ""

    # Handle booleans
    if isinstance(value, bool):
        return "✓" if value else "✗"

    # Handle lists/dicts as JSON
    if isinstance(value, (list, dict)):
        import json

        return json.dumps(value)[:50] + ("..." if len(str(value)) > 50 else "")

    # Truncate long strings
    str_value = str(value)
    if len(str_value) > 50:
        return str_value[:47] + "..."

    return str_value


def print_table(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> None:
    """
    Print data as a table to stdout.

    Args:
        data: List of dictionaries (rows)
        columns: Column names to include
        title: Table title
    """
    if not data:
        console.print("[yellow]No data to display[/yellow]")
        return

    table = Table(
        show_header=True,
        header_style="bold cyan",
        title=title,
        title_style="bold green",
    )

    # Get columns from first row if not specified
    if columns is None:
        columns = list(data[0].keys())

    # Add columns
    for col in columns:
        table.add_column(col)

    # Add rows
    for row in data:
        table.add_row(*[_format_cell(row.get(col, "")) for col in columns])

    console.print(table)