---
tags:
  - Guide
---

<div align="center" markdown>

<img src="https://raw.githubusercontent.com/onuralpszr/colabsh/main/assets/colabsh-logo.png" alt="colabsh logo" width="480">

# colabsh

A CLI tool for Google Colab. Execute code, download notebooks, and interact with
Google Colab from the terminal. Connects to Google Colab through your browser
via WebSocket. No API keys needed.

</div>

## Features

- :material-code-braces: **Execute code** - run Python snippets, scripts, or
  stdin directly on Colab
- :material-console: **Interactive REPL** - readline history, multiline input,
  persistent sessions
- :material-download: **Download notebooks** - export as `.ipynb` or `.py` with
  execution results
- :material-server: **Persistent server** - one browser tab serves all commands
- :material-monitor: **Headless mode** - works over SSH with port forwarding
- :material-history: **Local history** - track notebook sessions and access
  patterns
- :material-code-json: **JSON output** - pipe results to other tools or LLMs

## Quick start

!!! example "Get running in 30 seconds"

    === "pip"

        ```bash
        pip install colabsh
        ```

    === "uv"

        ```bash
        uvx colabsh exec "print('hello')"
        ```

    Then start using it:

    ```bash
    # Start the server (opens Google Colab in browser once)
    colabsh start

    # Execute code (reuses the same browser tab)
    colabsh exec "print('hello from Google Colab')"

    # Interactive REPL
    colabsh repl

    # Download notebook
    colabsh download notebook.ipynb

    # Stop when done
    colabsh stop
    ```

## How it works

```
Terminal                     Background Server              Browser
────────                     ─────────────────              ───────
colabsh start ──────────────▶ WebSocket server ◀──────────▶ Colab
colabsh exec "code" ────TCP──▶ routes to Colab ──────────▶ executes
colabsh exec "more" ────TCP──▶ same connection ──────────▶ executes
colabsh stop ───────────────▶ shuts down
```

1. `colabsh start` launches a background server and opens Colab in your browser
2. Colab's frontend connects back via WebSocket (MCP proxy protocol)
3. All subsequent commands go through this persistent connection
4. **One browser tab** serves all commands, no new tabs per command
5. The server auto-starts if you run `exec`/`repl` without starting first

!!! tip "Auto-start"

    You don't need to run `colabsh start` explicitly. Running `colabsh exec` or `colabsh repl` will auto-start the server if it's not already running.
