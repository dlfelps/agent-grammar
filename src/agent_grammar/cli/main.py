"""Top-level Click group for the ``agent-grammar`` console script."""

from __future__ import annotations

import click

from agent_grammar import __version__
from agent_grammar.cli.export import export_agent_docs


@click.group()
@click.version_option(version=__version__, prog_name="agent-grammar")
def cli() -> None:
    """agent-grammar: test-gated AI agent workflow documentation."""


cli.add_command(export_agent_docs)


if __name__ == "__main__":  # pragma: no cover
    cli()
