# SPDX-FileCopyrightText: 2026-present Onuralp SEZER <thunderbirdtr@gmail.com>
#
# SPDX-License-Identifier: Apache-2.0

import click

from colabsh.core.config import set_setting
from colabsh.core.history import (
    clear_history,
    get_history,
    get_history_path,
    get_notebook_history,
)
from colabsh.core.output import print_error, print_output


@click.group()
def history() -> None:
    """View and manage local notebook history."""


@history.command(name="list")
@click.pass_context
def list_history(ctx: click.Context) -> None:
    """List all tracked notebooks and access counts."""
    human: bool = ctx.obj["human"]
    data = get_history()
    notebooks = data.get("notebooks", {})

    if not notebooks:
        print_output({"notebooks": [], "message": "No history recorded"}, human=human)
        return

    output = []
    for nb_id, entry in notebooks.items():
        output.append(
            {
                "notebook_id": nb_id,
                "access_count": entry.get("access_count", 0),
                "created_at": entry.get("created_at"),
                "last_accessed_at": entry.get("last_accessed_at"),
            }
        )

    output.sort(key=lambda x: x.get("last_accessed_at", ""), reverse=True)
    print_output(output, human=human)


@history.command()
@click.argument("notebook_id")
@click.pass_context
def show(ctx: click.Context, notebook_id: str) -> None:
    """Show detailed history for a specific notebook."""
    human: bool = ctx.obj["human"]
    entry = get_notebook_history(notebook_id)
    if not entry:
        print_error(f"No history found for notebook {notebook_id}", human=human)
        raise SystemExit(1) from None
    print_output({"notebook_id": notebook_id, **entry}, human=human)


@history.command()
@click.confirmation_option(prompt="Delete all local history?")
@click.pass_context
def clear(ctx: click.Context) -> None:
    """Delete all local history."""
    human: bool = ctx.obj["human"]
    removed = clear_history()
    if removed:
        print_output({"status": "cleared", "message": "History deleted"}, human=human)
    else:
        print_output({"status": "empty", "message": "No history to delete"}, human=human)


@history.command()
@click.pass_context
def path(ctx: click.Context) -> None:
    """Show the history file path."""
    human: bool = ctx.obj["human"]
    print_output({"history_path": str(get_history_path())}, human=human)


@history.command()
@click.argument("state", type=click.Choice(["on", "off"]))
@click.pass_context
def toggle(ctx: click.Context, state: str) -> None:
    """Enable or disable local history tracking."""
    human: bool = ctx.obj["human"]
    enabled = state == "on"
    set_setting("history_enabled", enabled)
    status = "enabled" if enabled else "disabled"
    print_output(
        {"history_enabled": enabled, "message": f"History tracking {status}"},
        human=human,
    )
