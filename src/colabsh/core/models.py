# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Pydantic models for structured data across colabsh."""

from enum import Enum

from pydantic import BaseModel, Field


class ConnectionState(str, Enum):
    """WebSocket connection state."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    EXPIRED = "expired"


class ServerState(BaseModel):
    """Persisted server state written to server.json."""

    pid: int
    control_port: int = Field(alias="control_port")
    ws_port: int = Field(alias="ws_port")
    token: str
    headless: bool = False
    started_at: str = ""


class ConnectionInfo(BaseModel):
    """Connection status returned by ping."""

    connected: bool = False
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    connected_for_seconds: int | None = None
    last_close_code: int | None = None


class HealthResult(BaseModel):
    """Runtime health check result."""

    alive: bool = False
    has_gpu: bool = False
    gpu_name: str = ""
    connection_state: ConnectionState = ConnectionState.DISCONNECTED
    connected: bool = False
    error: str | None = None


class Settings(BaseModel):
    """User settings persisted to settings.json."""

    headless: bool = False
    auto: bool = False
    auto_show_browser: bool = False
    browser_profile: str | None = None
    history_enabled: bool = True
    gpu: str | None = None

    model_config = {"extra": "allow"}
