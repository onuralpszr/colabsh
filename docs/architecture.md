---
tags:
  - Architecture
  - Reference
---

# Architecture

## Overview

```
Terminal Client         Background Server              Google Colab Browser
─────────────────      ─────────────────              ──────────────────────
  CLI (Click)          TCP Control Server              WebSocket Connection
                       + ColabProxy (WebSocket)
  colabsh start   ───▶ Start server + open browser ◀── MCP handshake
  colabsh exec    ───▶ Route to active connection  ◀── JSON-RPC 2.0
  colabsh stop    ───▶ Shutdown gracefully
```

colabsh uses a client-server architecture where a persistent background server
maintains the WebSocket connection to Google Colab, and CLI commands communicate
with it over TCP.

## Project structure

??? abstract "Source tree"

    ```
    src/colabsh/
    ├── main.py              # Click CLI entry point
    ├── commands.py          # All commands (exec, repl, start, stop, download, tools)
    ├── constants.py         # App-wide constants (timeouts, URLs, protocol versions)
    ├── history.py           # History CLI subcommand group
    └── core/
        ├── cells.py         # Shared helpers for notebook cell parsing
        ├── config.py        # Platform config dirs, settings management
        ├── server.py        # Background server (WebSocket + TCP control)
        ├── proxy.py         # WebSocket + JSON-RPC to Colab frontend
        ├── output.py        # JSON/human-readable formatter
        ├── history.py       # Local usage tracking
        ├── repl.py          # Interactive REPL with readline
        └── qr.py            # QR code generation (optional)
    ```

## Components

### CLI layer

!!! info "`main.py` · `commands.py` · `history.py`"

    The CLI is built with [Click](https://click.palletsprojects.com/). The main entry point defines global options (`--json`, `--verbose`) and registers all subcommands. Commands communicate with the background server via TCP.

### Background server

!!! info "`core/server.py`"

    The `BackgroundServer` orchestrates two async servers:

    - **TCP Control Server** — accepts CLI commands as JSON messages, dispatches them to the proxy, and returns results
    - **WebSocket Proxy** — maintains the connection to Google Colab

    The server runs as a detached subprocess, writing its state (port, PID, token) to `server.json` so the CLI can find it.

### WebSocket proxy

!!! info "`core/proxy.py`"

    `ColabProxy` implements the MCP (Model Context Protocol) proxy protocol:

    - Runs a localhost WebSocket server
    - Validates connections with a random authentication token
    - Performs the MCP initialize handshake
    - Routes JSON-RPC 2.0 requests/responses between the CLI and Colab frontend

### Supporting modules

??? info "Cell helpers · Configuration · Output formatting"

    **Cell helpers** (`core/cells.py`)
    :   Shared utilities for parsing Colab's JSON-RPC responses — extracting cell IDs from `add_code_cell` results and cell data from `get_cells` results.

    **Configuration** (`core/config.py`)
    :   Platform-specific configuration using Click's `get_app_dir()`. Manages settings as a simple JSON file.

    **Output formatting** (`core/output.py`)
    :   Dual-format output: human-readable (default) or JSON (`--json`). Supports Pydantic models, dicts, lists, and scalars.

## Protocol

colabsh communicates with Google Colab using the **MCP proxy protocol** over
WebSocket:

1. Colab's frontend JavaScript connects to the local WebSocket server
2. colabsh performs the MCP initialize handshake
3. Tool calls (add cell, run cell, get cells, etc.) use JSON-RPC 2.0
4. Responses are routed back to the waiting CLI command

## Code execution flow

!!! example "What happens when you run `colabsh exec \"print('hello')\"`"

    1. CLI sends `#!json {"action": "exec", "args": {"code": "..."}}` to the TCP control server
    2. Control server calls `add_code_cell` via JSON-RPC to create a cell with the code
    3. Control server calls `run_code_cell` to execute the cell
    4. Control server calls `delete_cell` to clean up
    5. Execution output is returned to the CLI
