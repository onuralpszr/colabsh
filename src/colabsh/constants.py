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

# --- Reconnection ---
RECONNECT_MAX_RETRIES = 3
HEALTH_CHECK_TIMEOUT = 15.0  # seconds
HEALTH_CHECK_CODE = "\n".join(
    [
        "import json, os, subprocess",
        "info = {'has_gpu': os.path.exists('/dev/nvidia0'), 'gpu_name': ''}",
        "try:",
        "    r = subprocess.run(",
        "        ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],",
        "        capture_output=True, text=True, timeout=5,",
        "    )",
        "    if r.returncode == 0:",
        "        info['gpu_name'] = r.stdout.strip()",
        "except Exception:",
        "    pass",
        "print(json.dumps(info))",
    ]
)

# --- GPU / Runtime Type ---
# Labels must match the exact radio button text in Colab's "Change runtime type" dialog
GPU_TYPES: dict[str, str] = {
    "cpu": "None (CPU)",
    "t4": "T4 GPU",
    "a100": "A100 GPU",
    "v100": "v100 GPU",
    "l4": "L4 GPU",
    "tpu": "TPU v2",
}
GPU_CHOICES = list(GPU_TYPES.keys())
RUNTIME_DIALOG_TIMEOUT = 10_000  # milliseconds

# --- Playwright / Auto-connect ---
BROWSER_PROFILE_DIR = "browser-profile"
PLAYWRIGHT_NAV_TIMEOUT = 30_000  # milliseconds, page navigation
PLAYWRIGHT_ACCEPT_TIMEOUT = 30_000  # milliseconds, wait for accept button
MCP_ACCEPT_BUTTON_TEXT = "Connect"  # Colab MCP dialog accept button

# Common Chrome launch args shared by auto_connect and login
CHROME_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--no-default-browser-check",
]


# --- QR Code ---
QR_VERSION = 1
QR_BOX_SIZE = 1
QR_BORDER = 2
QR_BLOCK_CHAR = "\u2588\u2588"  # ██
QR_SPACE_CHAR = "  "
