"""
JSON output formatter.

Provides structured JSON output for scripting and integration.
"""

import json
from datetime import date, datetime
from io import StringIO
from typing import Any, Dict, List, Optional


class DateTimeEncoder(json.JSONEncoder):
    """
    JSON encoder that handles dates, datetimes, and other non-serializable types.
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return super().default(obj)


def format_json(
    data: Any,
    indent: int = 2,
    sort_keys: bool = False,
) -> str:
    """
    Format data as JSON string.

    Args:
        data: Data to serialize
        indent: Indentation spaces
        sort_keys: Whether to sort dictionary keys

    Returns:
        JSON string
    """
    return json.dumps(
        data,
        indent=indent,
        sort_keys=sort_keys,
        default=_json_serializable,
    )


def _json_serializable(obj: Any) -> Any:
    """Convert objects to JSON-serializable types"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, set):
        return list(obj)
    if hasattr(obj, "tolist"):  # numpy arrays
        return obj.tolist()
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def format_json_stream(
    data: List[Dict[str, Any]],
    fields: Optional[List[str]] = None,
) -> str:
    """
    Format data as JSON lines (streaming mode).

    Each record on its own line - useful for large datasets.

    Args:
        data: List of records
        fields: Fields to include (None = all)

    Returns:
        JSON lines string
    """
    output = StringIO()

    for record in data:
        if fields:
            filtered = {k: v for k, v in record.items() if k in fields}
        else:
            filtered = record

        output.write(json.dumps(filtered, default=_json_serializable))
        output.write("\n")

    return output.getvalue()


def print_json(data: Any) -> None:
    """Print data as JSON to stdout"""
    print(format_json(data))