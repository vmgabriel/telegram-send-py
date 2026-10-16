"""Shell completion script generation for the command-line interface.

The heavy lifting is delegated to Typer's own completion machinery, so the
generated scripts stay in sync with the installed Typer version.
"""

from __future__ import annotations

import typer
from typer.completion import get_completion_script

SUPPORTED_SHELLS: tuple[str, ...] = ("bash", "zsh", "fish")
"""Shells for which a completion script can be generated."""


def _complete_variable(prog_name: str) -> str:
    """Build the completion environment variable for a program name.

    Args:
        prog_name: The console script name, e.g. ``telegram-integration``.

    Returns:
        The variable Typer/Click uses to request completions, e.g.
        ``_TELEGRAM_INTEGRATION_COMPLETE``.
    """
    return f"_{prog_name.replace('-', '_').upper()}_COMPLETE"


def completion(
    ctx: typer.Context,
    shell: str = typer.Argument(
        "bash",
        help="Shell to generate completion for: bash, zsh or fish.",
    ),
    program: str | None = typer.Option(
        None,
        "--program",
        "-p",
        help="Program name to complete. Defaults to the current command name.",
    ),
) -> None:
    """Generate a shell completion script and print it to standard output.

    Examples:
        telegram-integration completion bash > telegram-integration.bash
        telegram-integration completion zsh  > _telegram-integration
        telegram-integration completion fish > telegram-integration.fish
    """
    normalized = shell.strip().lower()
    if normalized not in SUPPORTED_SHELLS:
        raise typer.BadParameter(
            f"Unsupported shell {shell!r}. Choose one of: {', '.join(SUPPORTED_SHELLS)}"
        )

    prog_name = program or ctx.find_root().info_name or "telegram-integration"
    script = get_completion_script(
        prog_name=prog_name,
        complete_var=_complete_variable(prog_name),
        shell=normalized,
    )
    typer.echo(script)


def register_completion(app: typer.Typer) -> None:
    """Register the hidden ``completion`` command on ``app``.

    Args:
        app: The Typer application to extend.
    """
    app.command("completion", hidden=True)(completion)
