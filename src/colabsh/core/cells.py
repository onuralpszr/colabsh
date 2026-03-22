# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Shared helpers for working with Colab notebook cells.

Utilities for parsing JSON-RPC responses from Google Colab's frontend,
extracting cell IDs and cell content from various response formats.
"""

import json
from typing import Any


def extract_cell_id(result: Any) -> str | None:
    """Extract cell ID from an add_code_cell result.

    Parses the JSON-RPC response content to find either a structured
    `newCellId` field or falls back to raw text.

    Args:
        result: The JSON-RPC response dict from `add_code_cell`.

    Returns:
        The cell ID string, or `None` if not found.
    """
    if not isinstance(result, dict):
        return None
    content = result.get("content", [])
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    try:
                        parsed = json.loads(text)
                        if isinstance(parsed, dict) and "newCellId" in parsed:
                            cell_id: str = parsed["newCellId"]
                            return cell_id
                    except (ValueError, json.JSONDecodeError):
                        pass
                    return str(text.strip())
    return None


def extract_cells(result: Any) -> list[dict[str, Any]]:
    """Extract cell data from a get_cells result.

    Looks in `structuredContent.cells` first, then falls back to
    parsing JSON from `content` text items.

    Args:
        result: The JSON-RPC response dict from `get_cells`.

    Returns:
        A list of cell dicts, or an empty list if none found.
    """
    if not isinstance(result, dict):
        return []

    structured = result.get("structuredContent", {})
    if isinstance(structured, dict):
        found = structured.get("cells", [])
        if isinstance(found, list):
            return found

    content = result.get("content", [])
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    try:
                        parsed = json.loads(text)
                        if isinstance(parsed, dict) and "cells" in parsed:
                            return parsed["cells"]  # type: ignore[no-any-return]
                        if isinstance(parsed, list):
                            return parsed
                    except (ValueError, json.JSONDecodeError):
                        pass
    return []


def join_source(source: Any) -> str:
    """Join cell source lines into a single string.

    Args:
        source: A string, list of strings, or other value.

    Returns:
        The joined source as a single string.
    """
    if isinstance(source, str):
        return source
    if isinstance(source, list):
        return "".join(source)
    return str(source)
