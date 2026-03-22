# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Platform-specific configuration management.

Handles config directory paths, settings persistence, and
platform detection for Linux, macOS, and Windows.

!!! info "Config locations"
    | Platform | Path |
    | -------- | ---- |
    | Linux    | `~/.config/colabsh/` |
    | macOS    | `~/Library/Application Support/colabsh/` |
    | Windows  | `C:\\Users\\<user>\\AppData\\Roaming\\colabsh\\` |
"""

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
from colabsh.core.models import Settings

# Platform-specific config directory
CONFIG_DIR = Path(click.get_app_dir(APP_NAME))
SETTINGS_PATH = CONFIG_DIR / SETTINGS_FILE
SERVER_STATE_PATH = CONFIG_DIR / SERVER_STATE_FILE
SERVER_LOG_PATH = CONFIG_DIR / SERVER_LOG_FILE
HISTORY_PATH = CONFIG_DIR / HISTORY_FILE


def ensure_config_dir() -> Path:
    """Create the config directory if it doesn't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def load_settings() -> Settings:
    """Load user settings from the config directory."""
    if not SETTINGS_PATH.exists():
        return Settings()
    with open(SETTINGS_PATH) as f:
        return Settings.model_validate(json.load(f))


def save_settings(settings: Settings) -> None:
    """Save user settings to the config directory."""
    ensure_config_dir()
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings.model_dump(), f, indent=2)


def get_setting(key: str, default: Any = None) -> Any:
    """Get a single setting value."""
    settings = load_settings()
    return getattr(settings, key, default)


def set_setting(key: str, value: Any) -> None:
    """Set a single setting value."""
    settings = load_settings()
    setattr(settings, key, value)
    save_settings(settings)
