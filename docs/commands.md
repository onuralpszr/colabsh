---
tags:
  - Reference
  - CLI
---

# Commands

## Global options

| Option            | Description                              |
| ----------------- | ---------------------------------------- |
| `--json`          | Output as JSON instead of human-readable |
| `-v`, `--verbose` | Enable debug logging                     |
| `--help`          | Show help and exit                       |

## Server management

### `colabsh start`

Start the background server and connect to Google Colab.

!!! example "Examples"

    ```bash
    colabsh start              # Open browser
    colabsh start --headless   # Print URL instead of opening browser
    colabsh start --qr         # Print QR code + URL (implies --headless)
    ```

| Option       | Description                                           |
| ------------ | ----------------------------------------------------- |
| `--headless` | Don't open browser print the connection URL instead |
| `--qr`       | Show QR code for the connection URL                   |

### `colabsh stop`

Stop the background server.

```bash
colabsh stop
```

### `colabsh status`

Check if the background server is running and connected.

!!! example "Examples"

    === "Human-readable"

        ```bash
        colabsh status
        # status: running
        # connected: true
        # pid: 12345
        ```

    === "JSON"

        ```bash
        colabsh --json status
        # {"status": "running", "connected": true, "pid": 12345}
        ```

## Code execution

### `colabsh exec`

Execute Python code on Google Colab.

!!! example "Examples"

    === "Inline code"

        ```bash
        colabsh exec "print('hello')"
        ```

    === "From file"

        ```bash
        colabsh exec -f script.py
        ```

    === "From stdin"

        ```bash
        echo "import sys; print(sys.version)" | colabsh exec -
        ```

| Option         | Description              |
| -------------- | ------------------------ |
| `-f`, `--file` | Execute code from a file |

!!! tip

    The code argument can be `-` to read from stdin, or omitted entirely when piping.

### `colabsh repl`

Start an interactive Python REPL on Google Colab.

```bash
colabsh repl
```

!!! info "REPL features"

    | Feature            | Details                                                          |
    | ------------------ | ---------------------------------------------------------------- |
    | Arrow keys         | Navigate previous commands (readline history)                    |
    | Persistent history | Saved across sessions                                            |
    | Multiline input    | Lines ending with `:` or `\` start a block (end with empty line) |
    | `/quit`            | Exit the REPL                                                    |
    | `/tools`           | List available Colab frontend tools                              |
    | `/cells`           | View current notebook cells                                      |

## Download

### `colabsh download`

Download the current Colab notebook.

!!! example "Examples"

    === "Jupyter notebook"

        ```bash
        colabsh download notebook.ipynb
        ```

    === "Python script"

        ```bash
        colabsh download script.py
        ```

    === "Execute then download"

        ```bash
        colabsh download output.ipynb -f analysis.py
        ```

| Option              | Description                                                   |
| ------------------- | ------------------------------------------------------------- |
| `--format`          | Output format: `py` or `ipynb` (auto-detected from extension) |
| `-f`, `--exec-file` | Execute a Python file before downloading                      |

## Other

### `colabsh tools`

List available tools from the Colab frontend.

```bash
colabsh tools
```

### `colabsh history`

View and manage local notebook history.

!!! example "History subcommands"

    ```bash
    colabsh history list             # Show tracked sessions
    colabsh history show <id>        # Show detailed history for a notebook
    colabsh history clear            # Delete all local history (with confirmation)
    colabsh history toggle on|off    # Enable/disable history tracking
    colabsh history path             # Show history file path
    ```
