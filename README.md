# colabsh

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/colabsh.svg)](https://pypi.org/project/colabsh/)
[![PyPI downloads](https://img.shields.io/pypi/dm/colabsh.svg)](https://pypistats.org/packages/colabsh)
[![Python versions](https://img.shields.io/pypi/pyversions/colabsh.svg)](https://pypi.org/project/colabsh/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

[![CI](https://img.shields.io/github/actions/workflow/status/onuralpszr/colabsh/ci.yml?branch=main)](https://github.com/onuralpszr/colabsh/actions)
[![coverage](https://codecov.io/gh/onuralpszr/colabsh/branch/main/graph/badge.svg)](https://codecov.io/gh/onuralpszr/colabsh)
[![Release](https://img.shields.io/github/v/release/onuralpszr/colabsh)](https://github.com/onuralpszr/colabsh/releases)
[![Dependabot Updates](https://github.com/onuralpszr/colabsh/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/onuralpszr/colabsh/actions/workflows/dependabot/dependabot-updates)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/onuralpszr/colabsh/main.svg)](https://results.pre-commit.ci/latest/github/onuralpszr/colabsh/main)
[![autofix enabled](https://shields.io/badge/autofix.ci-yes-success?logo=autofix-ci)](https://autofix.ci)
[![ruff](https://img.shields.io/badge/ruff-enabled-7b0cff?logo=ruff)](https://github.com/charliermarsh/ruff)
[![mypy](https://img.shields.io/badge/mypy-passing-brightgreen?logo=mypy)](https://github.com/onuralpszr/colabsh/actions)

[![stars](https://img.shields.io/github/stars/onuralpszr/colabsh?style=social)](https://github.com/onuralpszr/colabsh/stargazers)
[![forks](https://img.shields.io/github/forks/onuralpszr/colabsh?style=social)](https://github.com/onuralpszr/colabsh/network/members)
[![issues](https://img.shields.io/github/issues/onuralpszr/colabsh)](https://github.com/onuralpszr/colabsh/issues)
[![contributors](https://img.shields.io/github/contributors/onuralpszr/colabsh)](https://github.com/onuralpszr/colabsh/graphs/contributors)

</div>

A CLI tool for Google Colab. Execute code, download notebooks, and interact with
Google Colab from the terminal. Connects to Google Colab through your browser
via WebSocket — no API keys needed.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Commands](#commands)
- [Headless Mode](#headless-mode)
- [Security](#security)
- [Configuration](#configuration)
- [Development](#development)
- [Architecture](#architecture)
- [License](#license)

---

## Installation

| Method               | Command                                                                        |
| -------------------- | ------------------------------------------------------------------------------ |
| **pip**              | `pip install colabsh`                                                          |
| **uvx** (no install) | `uvx colabsh exec "print('hello')"`                                            |
| **From source**      | `git clone https://github.com/onuralpszr/colabsh.git && cd colabsh && uv sync` |

## Quick Start

```bash
# Start the server (opens Google Colab in browser once)
colabsh start

# Execute code (reuses the same browser tab)
colabsh exec "print('hello from Google Colab')"
colabsh exec -f script.py
echo "import sys; print(sys.version)" | colabsh exec -

# Interactive REPL with readline history
colabsh repl

# Download notebook
colabsh download notebook.ipynb
colabsh download script.py -f analysis.py

# Stop the server when done
colabsh stop
```

## How It Works

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
4. **One browser tab** serves all commands — no new tabs per command
5. The server auto-starts if you run `exec`/`repl` without starting first

## Commands

### Server

| Command                    | Description                             |
| -------------------------- | --------------------------------------- |
| `colabsh start`            | Start server and open browser           |
| `colabsh start --headless` | Print URL instead of opening browser    |
| `colabsh start --qr`       | Print QR code + URL for easy copy-paste |
| `colabsh stop`             | Stop the background server              |
| `colabsh status`           | Check connection state                  |

### Execute

| Command                         | Description         |
| ------------------------------- | ------------------- |
| `colabsh exec "code"`           | Execute inline code |
| `colabsh exec -f script.py`     | Execute a file      |
| `echo "code" \| colabsh exec -` | Execute from stdin  |
| `colabsh repl`                  | Interactive REPL    |

### REPL Features

| Feature            | Details                                                          |
| ------------------ | ---------------------------------------------------------------- |
| Arrow keys         | Navigate previous commands (readline history)                    |
| Persistent history | Saved across sessions                                            |
| Multiline input    | Lines ending with `:` or `\` start a block (end with empty line) |
| Commands           | `/quit`, `/tools`, `/cells`                                      |

### Download

| Command                                        | Description                               |
| ---------------------------------------------- | ----------------------------------------- |
| `colabsh download notebook.ipynb`              | Download as Jupyter notebook              |
| `colabsh download script.py`                   | Download as Python script                 |
| `colabsh download output.ipynb -f analysis.py` | Execute first, then download with results |

### Other

| Command                            | Description                                |
| ---------------------------------- | ------------------------------------------ |
| `colabsh tools`                    | List available Google Colab frontend tools |
| `colabsh history list`             | Show tracked sessions                      |
| `colabsh history show <id>`        | Show detailed history for a notebook       |
| `colabsh history clear`            | Delete all local history                   |
| `colabsh history toggle [on\|off]` | Enable/disable local history tracking      |
| `colabsh history path`             | Show history file path                     |
| `colabsh --json <command>`         | JSON output for scripting/LLM tools        |
| `colabsh -v <command>`             | Enable debug logging                       |

## Headless Mode

For SSH sessions, containers, or remote machines where there's no desktop
browser:

```bash
colabsh start --headless
```

This prints the connection URL instead of opening a browser. Open the URL on the
same machine in any browser.

### SSH Port Forwarding

To use colabsh on a remote server:

```bash
# On remote server
colabsh start --headless
# Output: https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=...&mcpProxyPort=45123

# On your local machine (forward the port)
ssh -L 45123:localhost:45123 remote-server

# Open the printed URL in your local browser
# It connects to localhost:45123 which is forwarded to the remote server

# Now run commands on the remote server
colabsh exec "print('running on remote')"
```

> **Why not LAN/phone access?** Google Colab's frontend JavaScript **always
> connects WebSocket to `localhost`** — this is hardcoded in Google's code. When
> you open the URL on a different device, the browser tries to connect to
> `localhost` on _that_ device, which doesn't have the colabsh server. The only
> workaround is **SSH port forwarding**, which makes the remote port appear as
> `localhost` on your local machine.

## Security

### What colabsh does

- Runs a **localhost-only** WebSocket server — not accessible from the network
- Uses a random **authentication token** for every session
- Communicates with Google Colab via Google's MCP proxy protocol
- Stores data locally in `~/.config/colabsh/` — nothing is sent to third parties

### What to be aware of

- The connection URL contains a secret token — treat it like a password
- Anyone with the URL can execute code in your Colab session
- The background server runs until you stop it (`colabsh stop`)
- Code execution happens on Google's Colab VMs, subject to Google's terms of
  service
- The Google Colab session has your Google account's permissions

### Token lifecycle

| Event           | Behavior                                                             |
| --------------- | -------------------------------------------------------------------- |
| `colabsh start` | A new random token is generated                                      |
| While running   | Token stored in `~/.config/colabsh/server.json` (user-readable only) |
| `colabsh stop`  | Token is deleted                                                     |

## Configuration

### Config directory

| Platform | Path                                       |
| -------- | ------------------------------------------ |
| Linux    | `~/.config/colabsh/`                       |
| macOS    | `~/Library/Application Support/colabsh/`   |
| Windows  | `C:\Users\<user>\AppData\Roaming\colabsh\` |

### Config files

| File            | Description                             |
| --------------- | --------------------------------------- |
| `server.json`   | Running server state (port, PID, token) |
| `server.log`    | Server logs                             |
| `settings.json` | User preferences (headless mode, etc.)  |
| `history.json`  | Local usage history                     |
| `repl_history`  | Readline command history                |

### Output format

Human-readable output is the default:

```bash
colabsh status
# status: running
# connected: true
# pid: 12345

colabsh --json status
# {"status": "running", "connected": true, "pid": 12345}
```

Use `--json` when piping to other tools or LLMs.

## Development

| Task                 | Command                          |
| -------------------- | -------------------------------- |
| Install dependencies | `uv sync`                        |
| Run tests            | `uv run pytest`                  |
| Lint                 | `uv run ruff check src/ tests/`  |
| Format               | `uv run ruff format src/ tests/` |
| Type check           | `uv run mypy src/colabsh/`       |

## Architecture

```
src/colabsh/
├── main.py              # Click CLI entry point
├── commands.py          # All commands (exec, repl, start, stop, download, tools)
├── history.py           # history list/show/clear/toggle
└── core/
    ├── config.py        # Platform config dirs, settings
    ├── server.py        # Background server (WebSocket + TCP control)
    ├── proxy.py         # WebSocket + JSON-RPC to Colab frontend
    ├── output.py        # JSON/human formatter
    ├── history.py       # Local usage tracking
    ├── repl.py          # Shared REPL with readline
    └── qr.py            # QR code generation (optional)
```

## License

Apache-2.0

## Inspiration

Inspired by [colab-mcp-proxy](https://github.com/googlecolab/colab-mcp-proxy)
but with a focus on CLI usability, persistent server, and local history.

## Disclaimer

This project has no affiliation with Google. It reverse-engineers Google Colab's
frontend protocol to enable terminal access. Use responsibly and in accordance
with Google's terms of service.
