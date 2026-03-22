# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Shared REPL logic with readline history support."""

import readline
from collections.abc import Callable
from typing import Any

import click

from colabsh.constants import (
    REPL_CONTINUATION_PROMPT,
    REPL_HISTORY_FILE,
    REPL_MAX_HISTORY,
    REPL_PROMPT,
    REPL_QUIT_COMMAND,
)
from colabsh.core.config import CONFIG_DIR

HISTORY_PATH = CONFIG_DIR / REPL_HISTORY_FILE


def setup_readline() -> None:
    """Configure readline with persistent history."""
    try:
        readline.set_history_length(REPL_MAX_HISTORY)
        if HISTORY_PATH.exists():
            readline.read_history_file(str(HISTORY_PATH))
    except OSError:
        pass


def save_readline() -> None:
    """Save readline history to disk."""
    try:
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        readline.write_history_file(str(HISTORY_PATH))
    except OSError:
        pass


def read_input(prompt: str) -> str:
    """Read a line of input using readline (supports arrow keys, history)."""
    return input(prompt)


def collect_multiline(line: str, buffer: list[str]) -> str | None:
    """Handle multiline input. Returns complete code when ready, None if still collecting."""
    if line.endswith((":", "\\")) or buffer:
        buffer.append(line)
        if line == "" and buffer:
            code = "\n".join(buffer)
            buffer.clear()
            return code
        return None
    return line


def run_repl_loop(
    execute_fn: Callable[[str], Any],
    format_fn: Callable[[Any], None],
    *,
    extra_commands: dict[str, Callable[[], Any]] | None = None,
) -> None:
    """Run an interactive REPL loop with readline history."""
    setup_readline()
    commands = extra_commands or {}

    buffer: list[str] = []
    try:
        while True:
            try:
                prompt = REPL_CONTINUATION_PROMPT if buffer else REPL_PROMPT
                line = read_input(prompt)
            except EOFError:
                break
            except KeyboardInterrupt:
                if buffer:
                    buffer.clear()
                    click.echo("")
                    continue
                click.echo(f"\nUse {REPL_QUIT_COMMAND} to exit.")
                continue

            stripped = line.strip()

            if not buffer and stripped == REPL_QUIT_COMMAND:
                break

            if not buffer and stripped.startswith("/"):
                cmd_name = stripped.split()[0]
                if cmd_name in commands:
                    commands[cmd_name]()
                    continue
                click.echo(f"Unknown command: {cmd_name}. Type {REPL_QUIT_COMMAND} to exit.")
                continue

            code = collect_multiline(line, buffer)
            if code is None:
                continue

            if not code.strip():
                continue

            try:
                result = execute_fn(code)
                format_fn(result)
            except Exception as e:
                click.echo(f"Error: {e}", err=True)
    finally:
        save_readline()
