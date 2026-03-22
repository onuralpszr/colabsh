# colabsh

A CLI tool for Google Colab. Execute code, download notebooks, and interact with Google Colab from the terminal.

Connects to Google Colab through your browser via WebSocket — no API keys needed.

## Installation

```bash
pip install colabsh
```

Or with uvx (no install):

```bash
uvx colabsh exec "print('hello')"
```

From source:

```bash
git clone https://github.com/osezer/colabsh.git
cd colabsh
uv sync
```

## Quick Start

```bash
# Start the server (opens Colab in browser once)
colabsh start

# Execute code (reuses the same browser tab)
colabsh exec "print('hello from Colab')"
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

```bash
colabsh start              # Start server + open browser
colabsh start --headless   # Print URL instead of opening browser
colabsh start --qr         # Print QR code + URL (for easy copy-paste)
colabsh stop               # Stop the background server
colabsh status             # Check connection state
```

### Execute

```bash
colabsh exec "code"        # Inline code
colabsh exec -f script.py  # Execute a file
echo "code" | colabsh exec -  # From stdin
colabsh repl               # Interactive REPL
```

### REPL

- **Arrow keys** navigate previous commands (readline history)
- **Persistent history** saved across sessions
- **Multiline input**: lines ending with `:` or `\` start a block (end with empty line)
- **Commands**: `/quit`, `/tools`, `/cells`

### Download

```bash
colabsh download notebook.ipynb                  # Download as Jupyter notebook
colabsh download script.py                       # Download as Python script
colabsh download output.ipynb -f analysis.py     # Execute first, then download with results
```

### Other

```bash
colabsh tools              # List available Google Colab frontend tools
colabsh history list       # Show tracked sessions
colabsh history toggle off # Disable local history tracking
colabsh --json status      # JSON output (for scripting/LLM tools)
```

## Headless Mode

For SSH sessions, containers, or remote machines where there's no desktop browser:

```bash
colabsh start --headless
```

This prints the connection URL instead of opening a browser. Open the URL on the same machine in any browser.

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

### Why Not LAN/Phone Access?

Google Colab's frontend JavaScript **always connects WebSocket to `localhost`** — this is hardcoded in Google's code. When you open the URL on a different device (phone, another computer), the browser tries to connect to `localhost` on that device, which doesn't have the colabsh server.

The only way to use colabsh from a different machine is **SSH port forwarding**, which makes the remote port appear as `localhost` on your local machine.

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
- Code execution happens on Google's Colab VMs, subject to Google's terms of service
- The Google Colab session has your Google account's permissions

### Token lifecycle

- A new random token is generated on every `colabsh start`
- The token is stored in `~/.config/colabsh/server.json` (only readable by you)
- Token is deleted when the server stops

## Config Directory

All data is stored locally:

| Platform | Path |
|----------|------|
| Linux | `~/.config/colabsh/` |
| macOS | `~/Library/Application Support/colabsh/` |
| Windows | `C:\Users\<user>\AppData\Roaming\colabsh\` |

Files:

- `server.json` — running server state (port, PID, token)
- `server.log` — server logs
- `settings.json` — user preferences (headless mode, etc.)
- `history.json` — local usage history
- `repl_history` — readline command history

## Output Format

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

```bash
uv sync
uv run pytest                     # Run tests
uv run ruff check src/ tests/     # Lint
uv run ruff format src/ tests/    # Format
uv run mypy src/colabsh/        # Type check
```

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
