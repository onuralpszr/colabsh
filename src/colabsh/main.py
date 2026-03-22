import logging

import click

from colabsh.commands import download, exec_cmd, login, repl_cmd, start, status, stop, tools
from colabsh.history import history


@click.group()
@click.option(
    "--json",
    "use_json",
    is_flag=True,
    default=False,
    help="Output as JSON instead of human-readable",
)
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging")
@click.pass_context
def cli(ctx: click.Context, use_json: bool, verbose: bool) -> None:
    """Colabsh execute code and interact with Google Colab from the terminal.

    !!! example "Quick start"
        ```bash
        colabsh start
        colabsh exec "print('hello')"
        colabsh stop
        ```
    """
    ctx.ensure_object(dict)
    ctx.obj["human"] = not use_json
    ctx.obj["verbose"] = verbose

    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")


cli.add_command(start)
cli.add_command(stop)
cli.add_command(status)
cli.add_command(exec_cmd, name="exec")
cli.add_command(repl_cmd, name="repl")
cli.add_command(download)
cli.add_command(tools)
cli.add_command(history)
cli.add_command(login)


if __name__ == "__main__":
    cli()
