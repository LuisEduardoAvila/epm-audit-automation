"""Output formatters for EPM Audit CLI."""

from typing import Any, Dict, List, Optional

from epm_audit_cli.output.table import format_table
from epm_audit_cli.output.json_fmt import format_json
from epm_audit_cli.output.csv_fmt import format_csv


def get_formatter(format_name: str):
    """
    Get output formatter by name.

    Args:
        format_name: One of 'table', 'json', 'csv'

    Returns:
        Formatter function

    Raises:
        ValueError: If format not supported
    """
    formatters = {
        "table": format_table,
        "json": format_json,
        "csv": format_csv,
    }

    if format_name not in formatters:
        raise ValueError(f"Unsupported format: {format_name}. Use one of: {list(formatters.keys())}")

    return formatters[format_name]


def format_output(
    data: Any,
    format_name: str = "table",
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
) -> str:
    """
    Format data for output.

    Args:
        data: Data to format (list of dicts or dict)
        format_name: Output format (table, json, csv)
        columns: Column names for table/csv (auto-detected if not provided)
        title: Optional title for table output

    Returns:
        Formatted string
    """
    formatter = get_formatter(format_name)

    if format_name == "table":
        return formatter(data, columns=columns, title=title)
    elif format_name == "csv":
        return formatter(data, columns=columns)
    else:
        return formatter(data)