"""
CSV output formatter.

Provides CSV output for import to Excel or databases.
"""

import csv
from io import StringIO
from typing import Any, Dict, List, Optional


def format_csv(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
    include_header: bool = True,
) -> str:
    """
    Format data as CSV string.

    Args:
        data: List of dictionaries (rows)
        columns: Column names to include (None = all keys from first row)
        include_header: Whether to include header row

    Returns:
        CSV string
    """
    if not data:
        return ""

    # Get columns from first row if not specified
    if columns is None:
        columns = list(data[0].keys())

    output = StringIO()
    writer = csv.writer(output, lineterminator="\n")

    if include_header:
        writer.writerow(columns)

    for row in data:
        writer.writerow([_format_csv_cell(row.get(col, "")) for col in columns])

    return output.getvalue()


def _format_csv_cell(value: Any) -> str:
    """Format a cell value for CSV"""
    if value is None:
        return ""

    if isinstance(value, bool):
        return "true" if value else "false"

    if isinstance(value, (list, dict)):
        import json

        return json.dumps(value)

    # Convert to string
    str_value = str(value)

    # Escape quotes and wrap if contains special chars
    if "," in str_value or '"' in str_value or "\n" in str_value:
        str_value = str_value.replace('"', '""')
        return f'"{str_value}"'

    return str_value


def print_csv(
    data: List[Dict[str, Any]],
    columns: Optional[List[str]] = None,
) -> None:
    """
    Print data as CSV to stdout.

    Args:
        data: List of dictionaries (rows)
        columns: Column names to include
    """
    print(format_csv(data, columns), end="")