# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

import json
import sys
from typing import IO, Any

from pydantic import BaseModel


def format_output(data: Any, *, human: bool = False) -> str:
    """Format data as JSON (default) or human-readable text.

    Supports dicts, lists, scalars, and Pydantic models.

    Args:
        data: The data to format (dict, list, scalar, or Pydantic model).
        human: If `True`, output human-readable key-value pairs.
            If `False` (default), output JSON.

    Returns:
        The formatted string.

    !!! example
        === "JSON (default)"
            ```python
            format_output({"status": "ok"})
            # '{"status": "ok"}'
            ```

        === "Human-readable"
            ```python
            format_output({"status": "ok"}, human=True)
            # 'status: ok'
            ```
    """
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
    """Format and print data to stdout (or a custom file).

    Args:
        data: The data to format and print.
        human: If `True`, print human-readable output.
        file: Output stream (defaults to `sys.stdout`).
    """
    print(format_output(data, human=human), file=file or sys.stdout)


def print_error(message: str, *, human: bool = False) -> None:
    """Print an error message to stderr.

    Args:
        message: The error message text.
        human: If `True`, print `Error: <message>`.
            If `False`, print `{"error": "<message>"}` as JSON.
    """
    if human:
        print(f"Error: {message}", file=sys.stderr)
    else:
        print(json.dumps({"error": message}), file=sys.stderr)
