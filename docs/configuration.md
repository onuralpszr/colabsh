---
tags:
  - Reference
  - Setup
---

# Configuration

## Config directory

All data is stored locally in a platform-specific directory:

=== ":material-linux: Linux"

    ```
    ~/.config/colabsh/
    ```

=== ":material-apple: macOS"

    ```
    ~/Library/Application Support/colabsh/
    ```

=== ":material-microsoft-windows: Windows"

    ```
    C:\Users\<user>\AppData\Roaming\colabsh\
    ```

## Config files

| File                 | Description                                        |
| -------------------- | -------------------------------------------------- |
| `server.json`        | Running server state (port, PID, token)            |
| `server.log`         | Server logs                                        |
| `settings.json`      | User preferences (headless mode, history tracking) |
| `history.json`       | Local usage history                                |
| `repl_history`       | Readline command history                           |
| `connection_url.txt` | Connection URL for headless mode                   |

## Settings

Settings are stored in `settings.json` and can be modified via commands:

| Setting           | Type | Default | Description                   |
| ----------------- | ---- | ------- | ----------------------------- |
| `headless`        | bool | `false` | Start server in headless mode |
| `history_enabled` | bool | `true`  | Enable local history tracking |

??? example "Managing history"

    ```bash
    colabsh history toggle off   # Disable history tracking
    colabsh history toggle on    # Enable history tracking
    colabsh history clear        # Delete all history data
    colabsh history path         # Show where history is stored
    ```

## Output format

!!! example "Output modes"

    === "Human-readable (default)"

        ```bash
        colabsh status
        ```

        ```
        status: running
        connected: true
        pid: 12345
        ```

    === "JSON"

        ```bash
        colabsh --json status
        ```

        ```json
        {"status": "running", "connected": true, "pid": 12345}
        ```

!!! tip

    Use `--json` when piping to other tools, scripts, or LLMs.
