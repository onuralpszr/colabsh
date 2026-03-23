---
tags:
  - Reference
  - CLI
---

# Commands

## Shell completion

Colabsh supports tab completion for all commands, options, and subcommands via
Click's built-in shell completion.

=== "Bash"

    Add to `~/.bashrc`:

    ```bash
    eval "$(_COLABSH_COMPLETE=bash_source colabsh)"
    ```

=== "Zsh"

    Add to `~/.zshrc`:

    ```bash
    eval "$(_COLABSH_COMPLETE=zsh_source colabsh)"
    ```

=== "Fish"

    Add to `~/.config/fish/config.fish`:

    ```fish
    _COLABSH_COMPLETE=fish_source colabsh | source
    ```

!!! tip "Faster startup with cached completion"

    Evaluating the completion script on every shell startup adds a small delay. You can generate the script once and source the file instead:

    === "Bash"

        ```bash
        _COLABSH_COMPLETE=bash_source colabsh > ~/.colabsh-complete.bash
        echo '. ~/.colabsh-complete.bash' >> ~/.bashrc
        ```

    === "Zsh"

        ```bash
        _COLABSH_COMPLETE=zsh_source colabsh > ~/.colabsh-complete.zsh
        echo '. ~/.colabsh-complete.zsh' >> ~/.zshrc
        ```

    === "Fish"

        ```fish
        _COLABSH_COMPLETE=fish_source colabsh > ~/.config/fish/completions/colabsh.fish
        ```

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

    === "Browser"

        ```bash
        colabsh start
        ```

    === "Auto (Playwright)"

        ```bash
        colabsh start --auto
        colabsh start --auto --gpu t4
        colabsh start --auto --show-browser
        ```

    === "Headless"

        ```bash
        colabsh start --headless
        colabsh start --qr
        ```

| Option             | Description                                          |
| ------------------ | ---------------------------------------------------- |
| `--auto`           | Fully headless with Playwright (no manual browser)   |
| `--gpu <type>`     | Select GPU on start (requires `--auto`)              |
| `--show-browser`   | Show the browser window when using `--auto`          |
| `--headless`       | Don't open browser, print the connection URL instead |
| `--qr`             | Show QR code for the connection URL                  |
| `--browser-profile`| Path to an existing browser profile directory        |

### `colabsh stop`

Stop the background server.

```bash
colabsh stop
```

### `colabsh status`

Check if the background server is running and connected.

!!! example "Examples"

    === "Basic"

        ```bash
        colabsh status
        # status: running
        # connected: true
        # connection_state: connected
        # connected_for_seconds: 42
        ```

    === "Health check"

        ```bash
        colabsh status --health
        # status: running
        # connected: true
        # runtime_type: Tesla T4
        # runtime_alive: true
        ```

    === "JSON"

        ```bash
        colabsh --json status --health
        ```

| Option     | Description                                 |
| ---------- | ------------------------------------------- |
| `--health` | Run full health check (GPU/CPU, uptime)     |

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

## GPU

### `colabsh gpu`

Change the Colab runtime GPU type on the fly. Requires the server to be running in `--auto` mode.

!!! example "Examples"

    ```bash
    colabsh gpu t4       # Switch to T4 GPU
    colabsh gpu a100     # Switch to A100 GPU
    colabsh gpu cpu      # Switch back to CPU
    ```

| Type   | Description |
| ------ | ----------- |
| `cpu`  | No GPU      |
| `t4`   | T4 GPU      |
| `v100` | V100 GPU    |
| `a100` | A100 GPU    |
| `l4`   | L4 GPU      |
| `tpu`  | TPU v2      |

!!! warning

    Changing GPU restarts the Colab runtime. Any variables or state in the notebook will be lost. The connection is re-established automatically.

## Authentication

### `colabsh login`

Sign in to Google for auto mode. Opens a visible browser window. The session is saved to the browser profile so `--auto` can reuse it.

```bash
colabsh login
```

!!! tip

    You only need to run `colabsh login` once. The session persists in `~/.config/colabsh/browser-profile/` until Google expires it.

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
