# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Central constants for colabsh. Change values here to affect the entire app."""

# --- App Identity ---
APP_NAME = "colabsh"

# --- Google Colab URLs ---
COLAB_URL = "https://colab.research.google.com"
COLAB_ALT_URL = "https://colab.google.com"
COLAB_NOTEBOOK_PATH = "/notebooks/empty.ipynb"

# --- MCP Protocol ---
MCP_PROTOCOL_VERSION = "2024-11-05"
JSONRPC_VERSION = "2.0"

# --- WebSocket Server ---
WS_HOST = "127.0.0.1"
WS_TOKEN_LENGTH = 16  # bytes for secrets.token_urlsafe()

# --- Timeouts (seconds) ---
CONNECTION_TIMEOUT = 90.0  # wait for Colab frontend to connect
RPC_REQUEST_TIMEOUT = 120.0  # wait for a JSON-RPC response
RECONNECT_TIMEOUT = 90.0  # wait during reconnect
SERVER_STARTUP_TIMEOUT = 15.0  # wait for background server to start
SERVER_POLL_INTERVAL = 0.3  # polling interval during startup
CONTROL_SOCKET_TIMEOUT = 130  # TCP socket timeout for control commands
CONTROL_READ_TIMEOUT = 5.0  # TCP read timeout for incoming request line
SHUTDOWN_POLL_INTERVAL = 0.2  # polling during graceful shutdown
SHUTDOWN_MAX_RETRIES = 20  # max retries during graceful shutdown

# --- TCP Control Server ---
CONTROL_HOST = "localhost"
CONTROL_RECV_BUFFER = 8192  # bytes

# --- REPL ---
REPL_PROMPT = ">>> "
REPL_CONTINUATION_PROMPT = "... "
REPL_MAX_HISTORY = 5000
REPL_QUIT_COMMAND = "/quit"

# --- File Names (relative to config dir) ---
SETTINGS_FILE = "settings.json"
SERVER_STATE_FILE = "server.json"
SERVER_LOG_FILE = "server.log"
HISTORY_FILE = "history.json"
REPL_HISTORY_FILE = "repl_history"
CONNECTION_URL_FILE = "connection_url.txt"

# --- Colab Tool Names ---
TOOL_ADD_CODE_CELL = "add_code_cell"
TOOL_RUN_CODE_CELL = "run_code_cell"
TOOL_DELETE_CELL = "delete_cell"
TOOL_GET_CELLS = "get_cells"

# --- Notebook Export ---
NOTEBOOK_FORMAT_VERSION = 4
NOTEBOOK_FORMAT_MINOR = 5
NOTEBOOK_KERNEL_NAME = "python3"
NOTEBOOK_KERNEL_DISPLAY = "Python 3"
NOTEBOOK_DEFAULT_PYTHON = "3.12.0"
NOTEBOOK_DEFAULT_OUTPUT = "notebook.py"

# --- Playwright / Auto-connect ---
BROWSER_PROFILE_DIR = "browser-profile"
PLAYWRIGHT_NAV_TIMEOUT = 30_000  # milliseconds, page navigation
PLAYWRIGHT_ACCEPT_TIMEOUT = 30_000  # milliseconds, wait for accept button
# Colab MCP dialog: "Cancel" and "Connect" buttons
MCP_ACCEPT_BUTTON_SELECTOR = "button"
MCP_ACCEPT_BUTTON_TEXT = "Connect"

# --- QR Code ---
QR_VERSION = 1
QR_BOX_SIZE = 1
QR_BORDER = 2
QR_BLOCK_CHAR = "\u2588\u2588"  # ██
QR_SPACE_CHAR = "  "
