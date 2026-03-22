# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Top-level CLI commands all use the persistent background server."""

import json
import sys
import time
from collections.abc import Callable
from typing import Any

import click

from colabsh.constants import (
    COLAB_NOTEBOOK_PATH,
    COLAB_URL,
    CONNECTION_URL_FILE,
    NOTEBOOK_DEFAULT_OUTPUT,
    NOTEBOOK_DEFAULT_PYTHON,
    NOTEBOOK_FORMAT_MINOR,
    NOTEBOOK_FORMAT_VERSION,
    NOTEBOOK_KERNEL_DISPLAY,
    NOTEBOOK_KERNEL_NAME,
    TOOL_ADD_CODE_CELL,
    TOOL_RUN_CODE_CELL,
)
from colabsh.core.cells import extract_cell_id, extract_cells, join_source
from colabsh.core.config import CONFIG_DIR, get_setting, set_setting
from colabsh.core.history import record_notebook_event
from colabsh.core.output import print_error, print_output
from colabsh.core.server import (
    is_server_running,
    read_server_state,
    send_control,
    start_server,
    stop_server,
)


def _is_headless() -> bool:
    """Check if headless mode is configured."""
    return get_setting("headless", False) is True


def _is_auto() -> bool:
    """Check if auto-connect mode is configured."""
    return get_setting("auto", False) is True


def _poll_connected(state: dict[str, Any], timeout: int = 90) -> bool:
    """Poll the server until Colab connects or timeout. Returns True if connected."""
    for _ in range(timeout):
        time.sleep(1)
        if send_control(state, "ping").get("connected"):
            return True
    return False


def _cli_handler(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap a CLI command body to catch exceptions and exit cleanly."""

    def wrapper(ctx: click.Context, *args: Any, **kwargs: Any) -> Any:
        human: bool = ctx.obj["human"]
        try:
            return fn(ctx, *args, human=human, **kwargs)
        except SystemExit:
            raise
        except RuntimeError as e:
            print_error(str(e), human=human)
            raise SystemExit(1) from None
        except Exception as e:
            print_error(str(e), human=human)
            raise SystemExit(1) from None

    return wrapper


def _ensure_server(human: bool) -> dict[str, Any]:
    """Ensure background server is running and connected. Auto-start/reconnect."""
    if is_server_running():
        state = read_server_state()
        if state:
            try:
                ping = send_control(state, "ping")
                if not ping.get("connected"):
                    result = send_control(state, "reconnect")
                    if result.get("auto"):
                        if result.get("connected"):
                            click.echo("Auto-reconnected via Playwright!", err=True)
                        else:
                            click.echo(
                                "Colab disconnected. Playwright is reconnecting...", err=True
                            )
                            if not _poll_connected(state):
                                print_error("Timed out waiting for Colab.", human=human)
                                raise SystemExit(1)
                            click.echo("Connected!", err=True)
                    elif result.get("headless"):
                        click.echo("Colab disconnected. Open this URL to reconnect:", err=True)
                        click.echo(result.get("url", ""), err=True)
                        click.echo("Waiting for connection...", err=True)
                        if not _poll_connected(state):
                            print_error("Timed out waiting for Colab.", human=human)
                            raise SystemExit(1)
                        click.echo("Connected!", err=True)
                    elif result.get("connected"):
                        click.echo("Reconnected!", err=True)
                    else:
                        print_error(
                            "Timed out waiting for Colab. Check the browser tab.", human=human
                        )
                        raise SystemExit(1)
            except SystemExit:
                raise
            except Exception:
                pass
            return state

    auto = _is_auto()
    headless = _is_headless()
    show_browser = get_setting("auto_show_browser", False) is True
    browser_profile = get_setting("browser_profile")
    if auto:
        click.echo("Starting server (auto-connect)...", err=True)
        headless = True
    elif headless:
        click.echo("Starting server (headless)...", err=True)
    else:
        click.echo("Starting server...", err=True)
        click.echo("Opening Colab in browser, please wait for connection...", err=True)

    state = start_server(
        headless=headless, auto=auto, show_browser=show_browser, browser_profile=browser_profile
    )
    if not state:
        print_error("Failed to start server. Check ~/.config/colabsh/server.log", human=human)
        raise SystemExit(1)

    if headless:
        _print_connection_url(state)

    click.echo("Server ready!", err=True)
    return state


def _print_connection_url(state: dict[str, Any]) -> None:
    """Print the connection URL (and optionally QR code) for headless mode."""
    url_path = CONFIG_DIR / CONNECTION_URL_FILE
    if url_path.exists():
        url = url_path.read_text().strip()
    else:
        # Construct from state
        url = (
            f"{COLAB_URL}{COLAB_NOTEBOOK_PATH}"
            f"#mcpProxyToken={state.get('token', '')}"
            f"&mcpProxyPort={state.get('ws_port', '')}"
            f"&mcpProxyHost=127.0.0.1"
        )

    click.echo("\nOpen this URL in any browser to connect:", err=True)
    click.echo(url, err=True)
    click.echo("", err=True)

    # Try QR code
    try:
        from colabsh.core.qr import render_qr

        qr = render_qr(url)
        if qr:
            click.echo("Or scan this QR code:", err=True)
            click.echo(qr, err=True)
            click.echo("", err=True)
    except Exception:
        pass


def _print_exec_output(result: Any) -> None:
    """Print execution output from structuredContent or content."""
    if not isinstance(result, dict):
        if result:
            click.echo(str(result))
        return

    # Check for error
    if result.get("isError"):
        content = result.get("content", [])
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("text"):
                    click.echo(f"Error: {item['text']}", err=True)
        return

    structured = result.get("structuredContent", {})
    if isinstance(structured, dict):
        outputs = structured.get("outputs", [])
        if outputs:
            for out in outputs:
                if not isinstance(out, dict):
                    continue
                texts = out.get("text", [])
                if isinstance(texts, list):
                    for t in texts:
                        click.echo(t, nl=not t.endswith("\n"))
                elif isinstance(texts, str):
                    click.echo(texts, nl=not texts.endswith("\n"))
            return

    content = result.get("content", [])
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                text = item.get("text", "")
                if text:
                    click.echo(text, nl=not text.endswith("\n"))
            else:
                click.echo(str(item))
    elif content:
        click.echo(str(content))


# --- Server management commands ---


@click.command()
@click.option(
    "--headless", is_flag=True, default=False, help="Don't open browser, print URL instead"
)
@click.option(
    "--qr",
    is_flag=True,
    default=False,
    help="Show QR code for the connection URL (implies --headless)",
)
@click.option(
    "--auto",
    is_flag=True,
    default=False,
    help="Auto-connect using Playwright (no manual browser interaction)",
)
@click.option(
    "--show-browser",
    is_flag=True,
    default=False,
    help="Show the browser window when using --auto (for debugging)",
)
@click.option(
    "--browser-profile",
    default=None,
    type=click.Path(exists=True, file_okay=False),
    help="Path to an existing browser profile (e.g. ~/.config/google-chrome/Default)",
)
@click.pass_context
def start(
    ctx: click.Context,
    headless: bool,
    qr: bool,
    auto: bool,
    show_browser: bool,
    browser_profile: str | None,
) -> None:
    """Start the background server and connect to Colab.

    By default opens Colab in your browser. Use `--headless` to print the URL
    instead (for SSH, containers, or remote machines). Use `--auto` for fully
    headless operation with Playwright (requires `pip install colabsh[auto]`).

    !!! warning "localhost only"
        The URL must be opened on the **same machine** where colabsh runs,
        because Colab's frontend connects to localhost. For remote access,
        use SSH port forwarding: `ssh -L PORT:localhost:PORT remote-host`

    !!! example "Usage"
        ```bash
        colabsh start --auto                              # Fully headless
        colabsh start --auto --show-browser               # Visible browser
        colabsh start --auto --browser-profile ~/.config/google-chrome  # Reuse Chrome profile
        colabsh start --headless                          # Print URL (SSH)
        colabsh start --qr                                # Print QR code + URL
        ```
    """
    human: bool = ctx.obj["human"]

    if browser_profile:
        auto = True

    if auto:
        from colabsh.core.browser import is_playwright_available

        if not is_playwright_available():
            print_error(
                "Playwright not installed. Run: pip install colabsh[auto] "
                "&& playwright install chromium",
                human=human,
            )
            raise SystemExit(1)
        headless = True
        set_setting("auto", True)
        set_setting("auto_show_browser", show_browser)
        if browser_profile:
            set_setting("browser_profile", browser_profile)

    if qr:
        headless = True

    if headless:
        set_setting("headless", True)

    if is_server_running():
        state = read_server_state()
        if state:
            try:
                ping_result = send_control(state, "ping")
                print_output({**state, **ping_result}, human=human)
            except Exception:
                print_output(state, human=human)
            return

    if auto:
        mode = "auto-connect, visible browser" if show_browser else "auto-connect"
        click.echo(f"Starting server ({mode})...", err=True)
        click.echo("Playwright is launching Chromium and navigating to Colab...", err=True)
    elif headless:
        click.echo("Starting server (headless)...", err=True)
    else:
        click.echo("Starting server...", err=True)
        click.echo("Opening Colab in browser...", err=True)

    state = start_server(
        headless=headless, auto=auto, show_browser=show_browser, browser_profile=browser_profile
    )
    if not state:
        print_error("Failed to start server. Check ~/.config/colabsh/server.log", human=human)
        raise SystemExit(1)

    if auto:
        _print_connection_url(state)
        click.echo("Playwright is handling the connection automatically.", err=True)
        # Wait for Playwright to click accept and WebSocket to connect
        click.echo("Waiting for Colab to connect...", err=True)
        if _poll_connected(state, timeout=30):
            click.echo("Connected!", err=True)
        else:
            click.echo("Connection pending. Check server log for details.", err=True)
    elif headless:
        _print_connection_url(state)
        click.echo("Server ready! Waiting for Colab to connect...", err=True)
    else:
        click.echo("Server ready! Waiting for Colab to connect...", err=True)

    try:
        ping_result = send_control(state, "ping")
        print_output({**state, **ping_result}, human=human)
    except Exception:
        print_output(state, human=human)


@click.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Stop the background server."""
    human: bool = ctx.obj["human"]
    if not is_server_running():
        print_output({"status": "not_running"}, human=human)
        return
    stop_server()
    print_output({"status": "stopped"}, human=human)


@click.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Check if the background server is running."""
    human: bool = ctx.obj["human"]
    if not is_server_running():
        print_output({"status": "not_running"}, human=human)
        return
    state = read_server_state()
    if not state:
        print_output({"status": "not_running"}, human=human)
        return
    try:
        ping = send_control(state, "ping")
        print_output({"status": "running", **state, **ping}, human=human)
    except Exception:
        print_output({"status": "running_no_response", **state}, human=human)


# --- Execution commands ---


@click.command(name="exec")
@click.argument("code", required=False)
@click.option("-f", "--file", "filepath", default=None, help="Execute code from a file")
@click.pass_context
def exec_cmd(ctx: click.Context, code: str | None, filepath: str | None) -> None:
    """Execute Python code on Colab.

    !!! example "Usage"
        === "Inline"
            ```bash
            colabsh exec "print('hello')"
            ```

        === "File"
            ```bash
            colabsh exec -f script.py
            ```

        === "Stdin"
            ```bash
            echo "print(1)" | colabsh exec -
            ```
    """

    @_cli_handler
    def _run(ctx: click.Context, *, human: bool) -> None:
        nonlocal code
        if filepath:
            with open(filepath) as f:
                code = f.read()
        elif code == "-" or (code is None and not sys.stdin.isatty()):
            code = sys.stdin.read()

        if not code:
            print_error(
                "No code provided. Pass code as argument, use -f, or pipe via stdin.",
                human=human,
            )
            raise SystemExit(1)

        state = _ensure_server(human)
        record_notebook_event("session", "exec")
        result = send_control(state, "exec", {"code": code})

        if human:
            _print_exec_output(result)
        else:
            print_output(result, human=False)

    _run(ctx)


@click.command(name="repl")
@click.pass_context
def repl_cmd(ctx: click.Context) -> None:
    """Start an interactive Python REPL on Colab.

    Supports readline history (arrow keys) and multiline input.

    !!! info "REPL commands"
        | Command  | Action                              |
        | -------- | ----------------------------------- |
        | `/quit`  | Exit the REPL                       |
        | `/tools` | List available Colab frontend tools |
        | `/cells` | View current notebook cells         |
    """
    from colabsh.core.repl import run_repl_loop

    @_cli_handler
    def _run(ctx: click.Context, *, human: bool) -> None:
        state = _ensure_server(human)
        record_notebook_event("session", "repl")

        if not send_control(state, "ping").get("connected"):
            click.echo("Waiting for Colab to connect in browser...", err=True)
            if not _poll_connected(state, timeout=60):
                print_error("Timed out waiting for Colab connection.", human=human)
                raise SystemExit(1)

        click.echo("Connected! Type /quit to exit, /tools to list tools, /cells to view cells.\n")

        def show_tools() -> None:
            tools = send_control(state, "list_tools")
            if isinstance(tools, list):
                for t in tools:
                    click.echo(f"  {t.get('name', '?')}: {t.get('description', '')[:80]}")
            else:
                click.echo(str(tools))

        run_repl_loop(
            lambda code: send_control(state, "exec", {"code": code}),
            _print_exec_output,
            extra_commands={
                "/tools": show_tools,
                "/cells": lambda: _print_exec_output(send_control(state, "get_cells")),
            },
        )

    _run(ctx)


@click.command()
@click.pass_context
def tools(ctx: click.Context) -> None:
    """List available tools from the Colab frontend."""

    @_cli_handler
    def _run(ctx: click.Context, *, human: bool) -> None:
        state = _ensure_server(human)
        print_output(send_control(state, "list_tools"), human=human)

    _run(ctx)


@click.command()
@click.argument("output", default=NOTEBOOK_DEFAULT_OUTPUT)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["py", "ipynb"], case_sensitive=False),
    default=None,
    help="Output format (auto-detected from extension)",
)
@click.option(
    "-f",
    "--exec-file",
    "exec_file",
    default=None,
    help="Execute a Python file first, then download the notebook with results",
)
@click.pass_context
def download(ctx: click.Context, output: str, fmt: str | None, exec_file: str | None) -> None:
    """Download the current Colab notebook.

    !!! example "Usage"
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
            colabsh download notebook.ipynb -f analysis.py
            ```
    """

    @_cli_handler
    def _run(ctx: click.Context, *, human: bool) -> None:
        resolved_fmt = fmt if fmt is not None else ("ipynb" if output.endswith(".ipynb") else "py")

        state = _ensure_server(human)
        record_notebook_event("session", "download")

        if exec_file:
            with open(exec_file) as f:
                code = f.read()
            click.echo(f"Executing {exec_file}...", err=True)
            add_result = send_control(
                state,
                "call_tool",
                {
                    "name": TOOL_ADD_CODE_CELL,
                    "arguments": {"cellIndex": 0, "language": "python", "code": code},
                },
            )
            cell_id = extract_cell_id(add_result)
            if cell_id:
                run_result = send_control(
                    state,
                    "call_tool",
                    {"name": TOOL_RUN_CODE_CELL, "arguments": {"cellId": cell_id}},
                )
                _print_exec_output(run_result)

        cells = [c for c in extract_cells(send_control(state, "get_cells")) if c.get("source")]

        if not cells:
            print_error("No cells found in notebook", human=human)
            raise SystemExit(1)

        (_save_as_python if resolved_fmt == "py" else _save_as_notebook)(cells, output)

        print_output(
            {"status": "downloaded", "path": output, "cells": len(cells), "format": resolved_fmt},
            human=human,
        )

    _run(ctx)


# --- File format helpers ---


def _save_as_python(cells: list[dict[str, Any]], path: str) -> None:
    """Save cells as a Python script."""
    parts: list[str] = []
    for cell in cells:
        cell_type = cell.get("cellType", cell.get("cell_type", ""))
        source = join_source(cell.get("source", cell.get("content", "")))
        if not source.strip():
            continue
        if cell_type == "code":
            if parts:
                parts.append("\n")
            parts.append(source)
        elif cell_type == "text":
            if parts:
                parts.append("\n")
            for text_line in source.splitlines():
                parts.append(f"# {text_line}\n")
    with open(path, "w") as f:
        f.write("".join(parts))


def _save_as_notebook(cells: list[dict[str, Any]], path: str) -> None:
    """Save cells as a Jupyter notebook (.ipynb)."""
    nb_cells: list[dict[str, Any]] = []
    for cell in cells:
        cell_type = cell.get("cellType", cell.get("cell_type", "code"))
        source = cell.get("source", cell.get("content", ""))
        source_lines = source.splitlines(keepends=True) if isinstance(source, str) else source

        nb_type = "markdown" if cell_type == "text" else "code"
        nb_cell: dict[str, Any] = {
            "cell_type": nb_type,
            "metadata": {},
            "source": source_lines,
        }
        if nb_type == "code":
            nb_cell["execution_count"] = None
            nb_cell["outputs"] = cell.get("outputs", [])
        nb_cells.append(nb_cell)

    notebook = {
        "nbformat": NOTEBOOK_FORMAT_VERSION,
        "nbformat_minor": NOTEBOOK_FORMAT_MINOR,
        "metadata": {
            "kernelspec": {
                "display_name": NOTEBOOK_KERNEL_DISPLAY,
                "language": "python",
                "name": NOTEBOOK_KERNEL_NAME,
            },
            "language_info": {"name": "python", "version": NOTEBOOK_DEFAULT_PYTHON},
        },
        "cells": nb_cells,
    }
    with open(path, "w") as f:
        json.dump(notebook, f, indent=2)


# --- Auth commands ---


@click.command()
def login() -> None:
    """Log in to Google for headless auto-connect mode.

    Opens a visible browser window for you to sign in to your Google
    account. The session is saved so that `colabsh start --auto` can
    reuse it without manual interaction.

    !!! example "Usage"
        ```bash
        colabsh login              # Sign in once
        colabsh start --auto       # Then use auto mode
        ```
    """
    import asyncio

    from colabsh.core.browser import is_playwright_available
    from colabsh.core.browser import login as browser_login

    if not is_playwright_available():
        click.echo(
            "Playwright not installed. Run: pip install colabsh[auto] "
            "&& playwright install chromium",
            err=True,
        )
        raise SystemExit(1)

    click.echo("Opening browser for Google login...", err=True)
    click.echo("Log in to your Google account, then come back here.", err=True)
    asyncio.run(browser_login())
    click.echo("Login session saved. You can now use 'colabsh start --auto'.", err=True)
