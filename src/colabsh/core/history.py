# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from colabsh.core.config import HISTORY_PATH, ensure_config_dir, get_setting


def is_history_enabled() -> bool:
    """Check if local history tracking is enabled (default: True)."""
    return get_setting("history_enabled", True) is True


def _load_history() -> dict[str, Any]:
    """Load the history file."""
    if not HISTORY_PATH.exists():
        return {"notebooks": {}}
    with open(HISTORY_PATH) as f:
        return json.load(f)  # type: ignore[no-any-return]


def _save_history(data: dict[str, Any]) -> None:
    """Save the history file."""
    ensure_config_dir()
    with open(HISTORY_PATH, "w") as f:
        json.dump(data, f, indent=2)


def record_notebook_event(
    notebook_id: str,
    event: str,
    *,
    variant: str | None = None,
    accelerator: str | None = None,
    endpoint: str | None = None,
) -> None:
    """Record an event for a notebook. Does nothing if history is disabled.

    Args:
        notebook_id: The notebook identifier.
        event: Event type (e.g. `"exec"`, `"repl"`, `"download"`, `"vm_assign"`).
        variant: Optional runtime variant (e.g. `"GPU"`).
        accelerator: Optional accelerator type (e.g. `"T4"`).
        endpoint: Optional endpoint identifier.

    !!! tip
        History tracking can be toggled with `colabsh history toggle on|off`.
    """
    if not is_history_enabled():
        return

    data = _load_history()
    notebooks: dict[str, Any] = data.setdefault("notebooks", {})

    now = datetime.now(timezone.utc).isoformat()

    if notebook_id not in notebooks:
        notebooks[notebook_id] = {
            "created_at": now,
            "access_count": 0,
            "events": [],
        }

    entry = notebooks[notebook_id]
    entry["access_count"] += 1
    entry["last_accessed_at"] = now

    event_record: dict[str, Any] = {"event": event, "timestamp": now}
    if variant:
        event_record["variant"] = variant
    if accelerator:
        event_record["accelerator"] = accelerator
    if endpoint:
        event_record["endpoint"] = endpoint

    entry["events"].append(event_record)

    _save_history(data)


def get_history() -> dict[str, Any]:
    """Return the full history data."""
    return _load_history()


def get_notebook_history(notebook_id: str) -> dict[str, Any] | None:
    """Return history for a specific notebook.

    Args:
        notebook_id: The notebook identifier.

    Returns:
        The history entry dict, or `None` if not found.
    """
    data = _load_history()
    result: dict[str, Any] | None = data.get("notebooks", {}).get(notebook_id)
    return result


def clear_history() -> bool:
    """Delete the history file.

    Returns:
        `True` if the file was deleted, `False` if it didn't exist.
    """
    if HISTORY_PATH.exists():
        HISTORY_PATH.unlink()
        return True
    return False


def get_history_path() -> Path:
    """Return the path to the history file."""
    return HISTORY_PATH
