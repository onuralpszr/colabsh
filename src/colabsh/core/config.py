# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Platform-specific configuration management."""

import json
from pathlib import Path
from typing import Any

import click

from colabsh.constants import (
    APP_NAME,
    HISTORY_FILE,
    SERVER_LOG_FILE,
    SERVER_STATE_FILE,
    SETTINGS_FILE,
)

# Platform-specific config directory:
#   Linux:   ~/.config/colabsh/
#   macOS:   ~/Library/Application Support/colabsh/
#   Windows: C:\Users\<user>\AppData\Roaming\colabsh\
CONFIG_DIR = Path(click.get_app_dir(APP_NAME))
SETTINGS_PATH = CONFIG_DIR / SETTINGS_FILE
SERVER_STATE_PATH = CONFIG_DIR / SERVER_STATE_FILE
SERVER_LOG_PATH = CONFIG_DIR / SERVER_LOG_FILE
HISTORY_PATH = CONFIG_DIR / HISTORY_FILE


def ensure_config_dir() -> Path:
    """Create the config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_settings() -> dict[str, Any]:
    """Load user settings from the config directory."""
    if not SETTINGS_PATH.exists():
        return {}
    with open(SETTINGS_PATH) as f:
        return json.load(f)  # type: ignore[no-any-return]


def save_settings(settings: dict[str, Any]) -> None:
    """Save user settings to the config directory."""
    ensure_config_dir()
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)


def get_setting(key: str, default: Any = None) -> Any:
    """Get a single setting value."""
    return load_settings().get(key, default)


def set_setting(key: str, value: Any) -> None:
    """Set a single setting value."""
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
