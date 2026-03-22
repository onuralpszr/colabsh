# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

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
    CONTROL_SOCKET_TIMEOUT,
    HEALTH_CHECK_CODE,
    RECONNECT_MAX_RETRIES,
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
from colabsh.core.cells import extract_cell_id
from colabsh.core.config import SERVER_LOG_PATH, SERVER_STATE_PATH, ensure_config_dir
from colabsh.core.models import ConnectionState, ServerState
from colabsh.core.proxy import ColabProxy


class ControlServer:
    """TCP server that accepts CLI commands and routes them to ColabProxy."""

    def __init__(self, proxy: ColabProxy, *, headless: bool = False, auto: bool = False) -> None:
        self.proxy = proxy
        self.headless = headless
        self.auto = auto
        self.port = 0
        self._server: asyncio.Server | None = None
        self._lock = asyncio.Lock()
        self._auto_page: object | None = None
        self._handlers: dict[str, Any] = {
            "ping": self._handle_ping,
            "exec": self._handle_exec,
            "list_tools": self._handle_list_tools,
            "get_cells": self._handle_get_cells,
            "call_tool": self._handle_call_tool,
            "reconnect": self._handle_reconnect,
            "health": self._handle_health,
            "change_gpu": self._handle_change_gpu,
            "shutdown": self._handle_shutdown,
        }

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
        handler = self._handlers.get(action)
        if not handler:
            return {"ok": False, "error": f"Unknown action: {action}"}

        try:
            result = await handler(args)
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # --- Handlers ---

    async def _handle_ping(self, args: dict[str, Any]) -> dict[str, Any]:
        info = self.proxy.connection_info().model_dump(exclude_none=True)
        return {"status": "running", **info}

    async def _run_ephemeral_cell(self, code: str) -> dict[str, Any]:
        """Create a cell, run it, delete it, and return the result."""
        add_result = await self.proxy.call_tool(
            TOOL_ADD_CODE_CELL, {"cellIndex": 0, "language": "python", "code": code}
        )
        cell_id = extract_cell_id(add_result)
        if not cell_id:
            return {"error": "Failed to create cell", "raw": add_result}

        run_result: dict[str, Any] = await self.proxy.call_tool(
            TOOL_RUN_CODE_CELL, {"cellId": cell_id}
        )

        with contextlib.suppress(Exception):
            await self.proxy.call_tool(TOOL_DELETE_CELL, {"cellId": cell_id})

        return run_result

    async def _handle_exec(self, args: dict[str, Any]) -> dict[str, Any]:
        if not self.proxy.is_connected:
            raise RuntimeError("Not connected to Colab. Open browser and connect.")
        code = args.get("code", "")
        if not code:
            raise ValueError("No code provided")
        return await self._run_ephemeral_cell(code)

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
        return await self.proxy.call_tool(args.get("name", ""), args.get("arguments", {}))

    async def _handle_health(self, args: dict[str, Any]) -> dict[str, Any]:
        """Run a health check on the Colab runtime to detect GPU/CPU."""
        conn = self.proxy.connection_info().model_dump(exclude_none=True)
        if not self.proxy.is_connected:
            return {"alive": False, **conn}
        try:
            run_result = await self._run_ephemeral_cell(HEALTH_CHECK_CODE)
            return {"alive": True, **conn, **self._parse_json_output(run_result)}
        except Exception as e:
            logging.warning("Health check failed: %s", e)
            return {"alive": False, "error": str(e), **conn}

    @staticmethod
    def _parse_json_output(result: dict[str, Any]) -> dict[str, Any]:
        """Extract JSON from structured cell output."""
        for out in result.get("structuredContent", {}).get("outputs", []):
            if not isinstance(out, dict):
                continue
            texts = out.get("text", [])
            text = texts[0] if isinstance(texts, list) and texts else ""
            if isinstance(text, str) and text.strip().startswith("{"):
                with contextlib.suppress(ValueError, json.JSONDecodeError):
                    return json.loads(text.strip())  # type: ignore[no-any-return]
        return {}

    async def _handle_change_gpu(self, args: dict[str, Any]) -> dict[str, Any]:
        """Change the Colab runtime GPU type via Playwright."""
        if not self.auto:
            raise RuntimeError("GPU selection requires --auto mode.")

        page = self._auto_page
        if not page:
            raise RuntimeError("No browser page available. Restart with --auto.")

        gpu_type = args.get("gpu_type", "")
        if not gpu_type:
            raise ValueError("No gpu_type provided.")

        from colabsh.core.browser import change_runtime_type

        await change_runtime_type(page, gpu_type)

        # Colab restarts the runtime after GPU change, which disconnects WebSocket.
        # Wait for reconnection.
        logging.info("Waiting for Colab to reconnect after GPU change...")
        connected = await self.proxy.wait_for_connection(timeout=RECONNECT_TIMEOUT)
        return {"changed": True, "gpu_type": gpu_type, "reconnected": connected}

    async def _handle_reconnect(self, args: dict[str, Any]) -> dict[str, Any]:
        """Reconnect to Colab with retry logic. Uses Playwright in auto mode."""
        url = self.proxy.get_connection_url()

        if self.proxy.state == ConnectionState.EXPIRED:
            return {
                "connected": False,
                "expired": True,
                "message": "Colab runtime expired.",
            }

        self.proxy.state = ConnectionState.RECONNECTING

        if self.auto:
            return await self._auto_reconnect(url)

        if self.headless:
            logging.info("Reconnect requested (headless) URL: %s", url)
            return {"url": url, "connected": False, "headless": True}

        self.proxy.open_browser()
        connected = await self.proxy.wait_for_connection(timeout=RECONNECT_TIMEOUT)
        return {"connected": connected, "headless": False}

    async def _auto_reconnect(self, url: str) -> dict[str, Any]:
        """Attempt auto-reconnect via Playwright with retries."""
        from colabsh.core.browser import auto_connect, close_page

        for attempt in range(1, RECONNECT_MAX_RETRIES + 1):
            logging.info("Auto-reconnect attempt %d/%d", attempt, RECONNECT_MAX_RETRIES)

            # Close stale browser page
            if self._auto_page:
                await close_page(self._auto_page)
                self._auto_page = None

            try:
                page = await auto_connect(url, headless=True)
                self._auto_page = page
                connected = await self.proxy.wait_for_connection(timeout=RECONNECT_TIMEOUT)
                if connected:
                    logging.info("Auto-reconnect succeeded on attempt %d", attempt)
                    return {"connected": True, "auto": True, "attempt": attempt}
                await close_page(page)
                self._auto_page = None
            except Exception as e:
                logging.error("Auto-reconnect attempt %d failed: %s", attempt, e)

        return {"connected": False, "auto": True, "exhausted_retries": True, "url": url}

    async def _handle_shutdown(self, args: dict[str, Any]) -> dict[str, str]:
        # Schedule shutdown on next loop iteration
        asyncio.get_event_loop().call_soon(self._request_shutdown)
        return {"status": "shutting_down"}

    def _request_shutdown(self) -> None:
        """Cancel all tasks to trigger graceful cleanup."""
        for task in asyncio.all_tasks():
            task.cancel()

    async def cleanup_browser(self) -> None:
        """Close any Playwright browser pages owned by this server."""
        if self._auto_page:
            from colabsh.core.browser import close_page

            await close_page(self._auto_page)
            self._auto_page = None

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()


class BackgroundServer:
    """Orchestrates the WebSocket proxy and TCP control server."""

    def __init__(
        self,
        *,
        headless: bool = False,
        auto: bool = False,
        show_browser: bool = False,
        browser_profile: str | None = None,
    ) -> None:
        self.proxy = ColabProxy()
        self.control = ControlServer(self.proxy, headless=headless, auto=auto)
        self.headless = headless
        self.auto = auto
        self.show_browser = show_browser
        self.browser_profile = browser_profile
        self._browser_page: object | None = None

    async def run(self) -> None:
        """Start both servers, write state file, open browser, run forever."""
        await self.proxy.start_server()
        await self.control.start()
        self._write_state()
        await self._open_connection()

        logging.info("Server started. Waiting for Colab connection...")

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, self._schedule_shutdown)

        try:
            await asyncio.Future()  # run forever
        except asyncio.CancelledError:
            pass
        finally:
            await self._cleanup()

    async def _open_connection(self) -> None:
        """Open browser or Playwright connection based on mode."""
        if self.auto:
            from colabsh.core.browser import auto_connect

            url = self.proxy.get_connection_url()
            mode = "visible" if self.show_browser else "headless"
            logging.info("Auto mode (%s): navigating to %s", mode, url)
            try:
                self._browser_page = await auto_connect(
                    url, headless=not self.show_browser, user_data_dir=self.browser_profile
                )
                # Share page with ControlServer for GPU changes etc.
                self.control._auto_page = self._browser_page
            except Exception as e:
                logging.error("Auto-connect failed: %s", e)
                self._write_connection_url()
                logging.info("Falling back to headless mode. Open the URL manually.")
        elif self.headless:
            self._write_connection_url()
        else:
            self.proxy.open_browser()

    def _write_connection_url(self) -> None:
        """Write the connection URL to a file for the CLI to read."""
        url = self.proxy.get_connection_url()
        logging.info("Headless mode, open this URL in a browser to connect:")
        logging.info(url)
        url_path = SERVER_STATE_PATH.parent / CONNECTION_URL_FILE
        url_path.write_text(url)

    def _write_state(self) -> None:
        ensure_config_dir()
        state = ServerState(
            pid=os.getpid(),
            control_port=self.control.port,
            ws_port=self.proxy.port,
            token=self.proxy.token,
            headless=self.headless,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        with open(SERVER_STATE_PATH, "w") as f:
            json.dump(state.model_dump(by_alias=True), f, indent=2)
        logging.info("State written to %s", SERVER_STATE_PATH)

    def _schedule_shutdown(self) -> None:
        """Signal handler: cancel all tasks to trigger cleanup."""
        for task in asyncio.all_tasks():
            task.cancel()

    async def _cleanup(self) -> None:
        """Clean up all resources: browser, servers, state files."""
        logging.info("Shutting down...")

        # Close Playwright browser (both from BackgroundServer and ControlServer)
        if self._browser_page is not None:
            from colabsh.core.browser import close_page

            await close_page(self._browser_page)
            self._browser_page = None
        await self.control.cleanup_browser()

        # Stop servers
        await self.control.stop()
        await self.proxy.stop()

        # Remove state files
        for path in [SERVER_STATE_PATH, SERVER_STATE_PATH.parent / CONNECTION_URL_FILE]:
            if path.exists():
                path.unlink()

        logging.info("Server stopped")


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
        _cleanup_stale_state()
        return False


def _cleanup_stale_state() -> None:
    """Remove stale state and connection URL files."""
    for path in [SERVER_STATE_PATH, SERVER_STATE_PATH.parent / CONNECTION_URL_FILE]:
        if path.exists():
            path.unlink()


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
        response = json.loads(sock.makefile().readline())

    if not response.get("ok"):
        raise RuntimeError(response.get("error", "Unknown server error"))
    res: dict[str, Any] = response.get("result", {})
    return res


def start_server(
    *,
    headless: bool = False,
    auto: bool = False,
    show_browser: bool = False,
    browser_profile: str | None = None,
) -> dict[str, Any] | None:
    """Start the background server as a subprocess. Returns state dict or None."""
    if is_server_running():
        return read_server_state()

    ensure_config_dir()

    cmd = [sys.executable, "-m", "colabsh.core.server"]
    if auto:
        cmd.append("--auto")
        headless = True
    if show_browser:
        cmd.append("--show-browser")
    if browser_profile:
        cmd.extend(["--browser-profile", browser_profile])
    if headless:
        cmd.append("--headless")

    log_file = open(SERVER_LOG_PATH, "a")  # noqa: SIM115
    subprocess.Popen(
        cmd,
        start_new_session=not show_browser,
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
    """Stop the background server gracefully, then force-kill if needed."""
    state = read_server_state()
    if not state:
        return False

    pid = state.get("pid", 0)

    # Try graceful shutdown first
    try:
        send_control(state, "shutdown")
        if _wait_for_exit(pid):
            return True
    except Exception:
        pass

    # Force kill the server process
    if pid:
        with contextlib.suppress(OSError, ProcessLookupError):
            os.kill(pid, signal.SIGKILL)
        _wait_for_exit(pid)

    _cleanup_stale_state()
    return True


def _wait_for_exit(pid: int) -> bool:
    """Poll until a process exits. Returns True if it exited."""
    for _ in range(SHUTDOWN_MAX_RETRIES):
        time.sleep(SHUTDOWN_POLL_INTERVAL)
        try:
            os.kill(pid, 0)
        except (OSError, ProcessLookupError):
            return True
    return False


# --- Entry point for subprocess ---

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", default=False)
    parser.add_argument("--auto", action="store_true", default=False)
    parser.add_argument("--show-browser", action="store_true", default=False)
    parser.add_argument("--browser-profile", default=None)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    async def _main() -> None:
        server = BackgroundServer(
            headless=args.headless,
            auto=args.auto,
            show_browser=args.show_browser,
            browser_profile=args.browser_profile,
        )
        await server.run()

    with contextlib.suppress(KeyboardInterrupt):
        asyncio.run(_main())
