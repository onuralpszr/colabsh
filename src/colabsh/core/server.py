"""Persistent background server: WebSocket for Colab + TCP control for CLI commands."""

import asyncio
import contextlib
import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any

from colabsh.constants import (
    CONNECTION_URL_FILE,
    CONTROL_HOST,
    CONTROL_READ_TIMEOUT,
    CONTROL_RECV_BUFFER,
    CONTROL_SOCKET_TIMEOUT,
    RECONNECT_TIMEOUT,
    SERVER_POLL_INTERVAL,
    SERVER_STARTUP_TIMEOUT,
    SHUTDOWN_MAX_RETRIES,
    SHUTDOWN_POLL_INTERVAL,
    TOOL_ADD_CODE_CELL,
    TOOL_DELETE_CELL,
    TOOL_GET_CELLS,
    TOOL_RUN_CODE_CELL,
)
from colabsh.core.config import SERVER_LOG_PATH, SERVER_STATE_PATH, ensure_config_dir
from colabsh.core.proxy import ColabProxy


class ControlServer:
    """TCP server that accepts CLI commands and routes them to ColabProxy."""

    def __init__(self, proxy: ColabProxy, *, headless: bool = False) -> None:
        self.proxy = proxy
        self.headless = headless
        self.port = 0
        self._server: asyncio.Server | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._server = await asyncio.start_server(self._handle_client, host=CONTROL_HOST, port=0)
        addr = self._server.sockets[0].getsockname()
        self.port = addr[1]
        logging.info("Control server on tcp://localhost:%s", self.port)

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            data = await asyncio.wait_for(reader.readline(), timeout=CONTROL_READ_TIMEOUT)
            if not data:
                return

            request = json.loads(data.decode())
            action = request.get("action", "")
            args = request.get("args", {})

            async with self._lock:
                response = await self._dispatch(action, args)

            writer.write((json.dumps(response) + "\n").encode())
            await writer.drain()
        except Exception as e:
            error_resp = {"ok": False, "error": str(e)}
            writer.write((json.dumps(error_resp) + "\n").encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def _dispatch(self, action: str, args: dict[str, Any]) -> dict[str, Any]:
        handlers: dict[str, Any] = {
            "ping": self._handle_ping,
            "exec": self._handle_exec,
            "list_tools": self._handle_list_tools,
            "get_cells": self._handle_get_cells,
            "call_tool": self._handle_call_tool,
            "reconnect": self._handle_reconnect,
            "shutdown": self._handle_shutdown,
        }

        handler = handlers.get(action)
        if not handler:
            return {"ok": False, "error": f"Unknown action: {action}"}

        try:
            result = await handler(args)
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _handle_ping(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"status": "running", "connected": self.proxy.is_connected}

    async def _handle_exec(self, args: dict[str, Any]) -> dict[str, Any]:
        if not self.proxy.is_connected:
            raise RuntimeError("Not connected to Colab. Open browser and connect.")

        import contextlib

        code = args.get("code", "")
        if not code:
            raise ValueError("No code provided")

        # add_code_cell → run_code_cell → delete_cell
        add_result = await self.proxy.call_tool(
            TOOL_ADD_CODE_CELL, {"cellIndex": 0, "language": "python", "code": code}
        )
        cell_id = _extract_cell_id(add_result)
        if not cell_id:
            return {"error": "Failed to create cell", "raw": add_result}

        run_result: dict[str, Any] = await self.proxy.call_tool(
            TOOL_RUN_CODE_CELL, {"cellId": cell_id}
        )

        with contextlib.suppress(Exception):
            await self.proxy.call_tool(TOOL_DELETE_CELL, {"cellId": cell_id})

        return run_result

    async def _handle_list_tools(self, args: dict[str, Any]) -> list[dict[str, Any]]:
        if not self.proxy.is_connected:
            raise RuntimeError("Not connected to Colab")
        return await self.proxy.list_tools()

    async def _handle_get_cells(self, args: dict[str, Any]) -> Any:
        if not self.proxy.is_connected:
            raise RuntimeError("Not connected to Colab")
        return await self.proxy.call_tool(TOOL_GET_CELLS, {"includeOutputs": True})

    async def _handle_call_tool(self, args: dict[str, Any]) -> Any:
        if not self.proxy.is_connected:
            raise RuntimeError("Not connected to Colab")
        name = args.get("name", "")
        arguments = args.get("arguments", {})
        return await self.proxy.call_tool(name, arguments)

    async def _handle_reconnect(self, args: dict[str, Any]) -> dict[str, Any]:
        """Reconnect to Colab. In headless mode, returns URL instead of opening browser."""
        url = self.proxy.get_connection_url()
        if self.headless:
            logging.info("Reconnect requested (headless) — URL: %s", url)
            return {"url": url, "connected": False, "headless": True}
        self.proxy.open_browser()
        connected = await self.proxy.wait_for_connection(timeout=RECONNECT_TIMEOUT)
        return {"connected": connected, "headless": False}

    async def _handle_shutdown(self, args: dict[str, Any]) -> dict[str, str]:
        asyncio.get_event_loop().call_soon(self._trigger_shutdown)
        return {"status": "shutting_down"}

    def _trigger_shutdown(self) -> None:
        asyncio.get_event_loop().call_soon(asyncio.get_event_loop().stop)

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()


class BackgroundServer:
    """Orchestrates the WebSocket proxy and TCP control server."""

    def __init__(self, *, headless: bool = False) -> None:
        self.proxy = ColabProxy()
        self.control = ControlServer(self.proxy, headless=headless)
        self.headless = headless

    async def run(self) -> None:
        """Start both servers, write state file, open browser, run forever."""
        await self.proxy.start_server()
        await self.control.start()

        self._write_state()

        if self.headless:
            url = self.proxy.get_connection_url()
            logging.info("Headless mode — open this URL in a browser to connect:")
            logging.info(url)
            # Write URL to a separate file for the CLI to read
            url_path = SERVER_STATE_PATH.parent / CONNECTION_URL_FILE
            url_path.write_text(url)
        else:
            self.proxy.open_browser()

        logging.info("Server started. Waiting for Colab connection...")

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: loop.stop())

        try:
            await asyncio.Future()  # run forever
        except asyncio.CancelledError:
            pass
        finally:
            await self._cleanup()

    def _write_state(self) -> None:
        ensure_config_dir()
        state = {
            "pid": os.getpid(),
            "control_port": self.control.port,
            "ws_port": self.proxy.port,
            "token": self.proxy.token,
            "headless": self.headless,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(SERVER_STATE_PATH, "w") as f:
            json.dump(state, f, indent=2)
        logging.info("State written to %s", SERVER_STATE_PATH)

    async def _cleanup(self) -> None:
        logging.info("Shutting down...")
        await self.control.stop()
        await self.proxy.stop()
        if SERVER_STATE_PATH.exists():
            SERVER_STATE_PATH.unlink()
        logging.info("Server stopped")


def _extract_cell_id(result: Any) -> str | None:
    """Extract cell ID from add_code_cell result."""
    if not isinstance(result, dict):
        return None
    content = result.get("content", [])
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    try:
                        parsed = json.loads(text)
                        if isinstance(parsed, dict) and "newCellId" in parsed:
                            cell_id: str = parsed["newCellId"]
                            return cell_id
                    except (ValueError, json.JSONDecodeError):
                        pass
                    return str(text.strip())
    return None


# --- Client-side helpers (used by CLI commands) ---


def read_server_state() -> dict[str, Any] | None:
    """Read the server state file. Returns None if not found or corrupt."""
    if not SERVER_STATE_PATH.exists():
        return None
    try:
        with open(SERVER_STATE_PATH) as f:
            return json.load(f)  # type: ignore[no-any-return]
    except (json.JSONDecodeError, OSError):
        return None


def is_server_running() -> bool:
    """Check if the background server is alive."""
    state = read_server_state()
    if not state:
        return False
    pid = state.get("pid")
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        # Stale state file — clean up
        if SERVER_STATE_PATH.exists():
            SERVER_STATE_PATH.unlink()
        return False


def send_control(
    state: dict[str, Any], action: str, args: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Send a command to the background server via TCP."""
    import socket

    request: dict[str, Any] = {"action": action}
    if args:
        request["args"] = args

    with socket.create_connection(
        (CONTROL_HOST, state["control_port"]), timeout=CONTROL_SOCKET_TIMEOUT
    ) as sock:
        sock.settimeout(CONTROL_SOCKET_TIMEOUT)
        sock.sendall((json.dumps(request) + "\n").encode())
        data = b""
        while True:
            chunk = sock.recv(CONTROL_RECV_BUFFER)
            if not chunk:
                break
            data += chunk

    response = json.loads(data.decode())
    if not response.get("ok"):
        raise RuntimeError(response.get("error", "Unknown server error"))
    res: dict[str, Any] = response.get("result", {})
    return res


def start_server(*, headless: bool = False) -> dict[str, Any] | None:
    """Start the background server as a subprocess. Returns state dict or None."""
    if is_server_running():
        return read_server_state()

    ensure_config_dir()

    cmd = [sys.executable, "-m", "colabsh.core.server"]
    if headless:
        cmd.append("--headless")

    log_file = open(SERVER_LOG_PATH, "a")  # noqa: SIM115
    subprocess.Popen(
        cmd,
        start_new_session=True,
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

    # Poll for state file
    start_time = time.monotonic()
    while time.monotonic() - start_time < SERVER_STARTUP_TIMEOUT:
        time.sleep(SERVER_POLL_INTERVAL)
        state = read_server_state()
        if state:
            return state

    return None


def stop_server() -> bool:
    """Stop the background server gracefully."""
    state = read_server_state()
    if not state:
        return False
    try:
        send_control(state, "shutdown")
        # Wait for process to exit
        pid = state.get("pid", 0)
        for _ in range(SHUTDOWN_MAX_RETRIES):
            time.sleep(SHUTDOWN_POLL_INTERVAL)
            try:
                os.kill(pid, 0)
            except (OSError, ProcessLookupError):
                break
        return True
    except Exception:
        # Force kill if graceful shutdown fails
        pid = state.get("pid", 0)
        if pid:
            with contextlib.suppress(OSError, ProcessLookupError):
                os.kill(pid, signal.SIGKILL)
        if SERVER_STATE_PATH.exists():
            SERVER_STATE_PATH.unlink()
        return True


# --- Entry point for subprocess ---

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", default=False)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    async def _main() -> None:
        server = BackgroundServer(headless=args.headless)
        await server.run()

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_main())
