import json
import sys
from typing import IO, Any

from pydantic import BaseModel


def format_output(data: Any, *, human: bool = False) -> str:
    """Format data as JSON (default) or human-readable text."""
    if isinstance(data, BaseModel):
        data = data.model_dump(by_alias=True)

    if human:
        return _format_human(data)
    return json.dumps(data, indent=2, default=str)


def _format_human(data: Any) -> str:
    if isinstance(data, dict):
        lines: list[str] = []
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{k}:")
                for sub_line in _format_human(v).splitlines():
                    lines.append(f"  {sub_line}")
            else:
                lines.append(f"{k}: {v}")
        return "\n".join(lines)
    elif isinstance(data, list):
        if not data:
            return "(empty)"
        lines = []
        for i, item in enumerate(data):
            lines.append(f"[{i}]")
            for sub_line in _format_human(item).splitlines():
                lines.append(f"  {sub_line}")
        return "\n".join(lines)
    return str(data)


def print_output(data: Any, *, human: bool = False, file: IO[str] | None = None) -> None:
    """Format and print data."""
    print(format_output(data, human=human), file=file or sys.stdout)


def print_error(message: str, *, human: bool = False) -> None:
    """Print an error message."""
    if human:
        print(f"Error: {message}", file=sys.stderr)
    else:
        print(json.dumps({"error": message}), file=sys.stderr)
