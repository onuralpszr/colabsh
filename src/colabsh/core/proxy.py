# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

"""WebSocket proxy to Colab frontend using raw JSON-RPC 2.0."""

import asyncio
import json
import logging
import secrets
import time
import webbrowser
from typing import Any

from websockets.asyncio.server import ServerConnection, serve
from websockets.datastructures import Headers
from websockets.http11 import Request, Response
from websockets.typing import Subprotocol

from colabsh.__about__ import __version__
from colabsh.constants import (
    APP_NAME,
    COLAB_ALT_URL,
    COLAB_NOTEBOOK_PATH,
    COLAB_URL,
    CONNECTION_TIMEOUT,
    JSONRPC_VERSION,
    MCP_PROTOCOL_VERSION,
    RPC_REQUEST_TIMEOUT,
    WS_HOST,
    WS_TOKEN_LENGTH,
)
from colabsh.core.models import ConnectionInfo, ConnectionState


class ColabProxy:
    """Connect to Colab frontend via WebSocket and call tools using JSON-RPC 2.0."""

    def __init__(self) -> None:
        self._server: Any = None
        self._ws: ServerConnection | None = None
        self._connection_ready = asyncio.Event()
        self._responses: dict[int, asyncio.Future[dict[str, Any]]] = {}
        self._next_id = 1
        self.port = 0
        self.token = secrets.token_urlsafe(WS_TOKEN_LENGTH)
        self._initialized = False
        self.state = ConnectionState.DISCONNECTED
        self.connected_at: float | None = None
        self.disconnected_at: float | None = None
        self.last_close_code: int | None = None

    def _validate_request(self, connection: ServerConnection, request: Request) -> Response | None:
        if request.path and f"access_token={self.token}" in request.path:
            return None
        auth_header = request.headers.get("Authorization", "")
        if auth_header:
            parts = auth_header.split(None, 1)
            if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1] == self.token:
                return None
        return Response(403, "Forbidden", Headers([]))

    async def _do_initialize(self) -> None:
        """Run the MCP initialize handshake with the Colab frontend."""
        await self._send_request(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": APP_NAME, "version": __version__},
            },
        )
        await self._send_notification("notifications/initialized")
        self._initialized = True
        logging.info("MCP handshake complete")

    async def _read_messages(self, websocket: ServerConnection) -> None:
        """Read messages from WebSocket and route responses to waiting futures."""
        async for raw_msg in websocket:
            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError:
                continue
            msg_id = msg.get("id")
            if msg_id is not None and msg_id in self._responses:
                self._responses[msg_id].set_result(msg)
            else:
                logging.debug("Received: %s", json.dumps(msg)[:200])

    async def _handle_connection(self, websocket: ServerConnection) -> None:
        """Accept a Colab frontend connection. Supports reconnection."""
        if self._ws is not None:
            await websocket.close(code=1013, reason="Already connected")
            return

        self._ws = websocket
        self.state = ConnectionState.CONNECTING
        self._connection_ready.set()
        logging.info("Colab frontend connected")

        reader_task = asyncio.create_task(self._read_messages(websocket))

        try:
            await self._do_initialize()
            self.state = ConnectionState.CONNECTED
            self.connected_at = time.monotonic()
        except Exception as e:
            logging.error("MCP handshake failed: %s", e)
            reader_task.cancel()
            self._ws = None
            self.state = ConnectionState.DISCONNECTED
            self._connection_ready.clear()
            return

        try:
            await reader_task
        except Exception as e:
            logging.info("Connection closed: %s", e)
        finally:
            close_code = getattr(websocket, "close_code", None)
            self.last_close_code = close_code
            self._ws = None
            self._initialized = False
            self._connection_ready.clear()
            self.disconnected_at = time.monotonic()
            if close_code == 1001:
                self.state = ConnectionState.EXPIRED
                logging.info("Colab runtime expired (close code 1001)")
            else:
                self.state = ConnectionState.DISCONNECTED
                logging.info("Colab frontend disconnected (close code: %s)", close_code)

    async def _send_request(
        self, method: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if not self._ws:
            raise RuntimeError("Not connected to Colab")

        msg_id = self._next_id
        self._next_id += 1

        request: dict[str, Any] = {
            "jsonrpc": JSONRPC_VERSION,
            "id": msg_id,
            "method": method,
        }
        if params is not None:
            request["params"] = params

        future: asyncio.Future[dict[str, Any]] = asyncio.get_event_loop().create_future()
        self._responses[msg_id] = future

        await self._ws.send(json.dumps(request))

        try:
            result = await asyncio.wait_for(future, timeout=RPC_REQUEST_TIMEOUT)
        finally:
            self._responses.pop(msg_id, None)

        if "error" in result:
            err = result["error"]
            raise RuntimeError(f"RPC error {err.get('code', '?')}: {err.get('message', str(err))}")

        res: dict[str, Any] = result.get("result", {})
        return res

    async def _send_notification(self, method: str, params: dict[str, Any] | None = None) -> None:
        if not self._ws:
            raise RuntimeError("Not connected to Colab")
        msg: dict[str, Any] = {"jsonrpc": JSONRPC_VERSION, "method": method}
        if params is not None:
            msg["params"] = params
        await self._ws.send(json.dumps(msg))

    # --- Public API ---

    async def start_server(self) -> None:
        """Start the WebSocket server (does NOT open browser or wait)."""
        self._server = await serve(
            self._handle_connection,
            host=WS_HOST,
            port=0,
            subprotocols=[Subprotocol("mcp")],
            origins=[COLAB_URL, COLAB_ALT_URL],  # type: ignore[list-item]
            process_request=self._validate_request,
        )
        self.port = self._server.sockets[0].getsockname()[1]
        logging.info("WebSocket server on ws://%s:%s", WS_HOST, self.port)

    def get_connection_url(self) -> str:
        """Return the Colab URL with proxy connection params."""
        return (
            f"{COLAB_URL}{COLAB_NOTEBOOK_PATH}#mcpProxyToken={self.token}&mcpProxyPort={self.port}"
        )

    def open_browser(self) -> None:
        """Open Colab in the browser with proxy connection params."""
        webbrowser.open_new(self.get_connection_url())

    async def wait_for_connection(self, timeout: float = CONNECTION_TIMEOUT) -> bool:
        """Wait for the Colab frontend to connect."""
        try:
            await asyncio.wait_for(self._connection_ready.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False

    async def list_tools(self) -> list[dict[str, Any]]:
        result = await self._send_request("tools/list")
        tools: list[dict[str, Any]] = result.get("tools", [])
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        return await self._send_request("tools/call", {"name": name, "arguments": arguments or {}})

    async def stop(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        self._initialized = False

    @property
    def is_connected(self) -> bool:
        return self._ws is not None and self._initialized

    def connection_info(self) -> ConnectionInfo:
        """Return connection state as a Pydantic model."""
        return ConnectionInfo(
            connected=self.is_connected,
            connection_state=self.state,
            connected_for_seconds=(
                round(time.monotonic() - self.connected_at)
                if self.connected_at is not None and self.is_connected
                else None
            ),
            last_close_code=self.last_close_code,
        )
