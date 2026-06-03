"""``agent-grammar export-agent-docs`` subcommand."""

from __future__ import annotations

from pathlib import Path

import click
from jinja2 import Environment, PackageLoader, select_autoescape

PLATFORMS = ("cursor", "claude", "copilot", "gemini")


def _build_environment() -> Environment:
    return Environment(
        loader=PackageLoader("agent_grammar", "templates"),
        autoescape=select_autoescape(default=False),
        trim_blocks=False,
        lstrip_blocks=False,
        keep_trailing_newline=True,
    )


@click.command("export-agent-docs")
@click.option(
    "--base-url",
    required=True,
    help="Production base URL of the API (e.g. https://api.example.com).",
)
@click.option(
    "--api-version",
    default="v1",
    show_default=True,
    help="API version namespace (used in the fetch URL and local file path).",
)
@click.option(
    "--output-dir",
    default="./agent-docs",
    show_default=True,
    type=click.Path(file_okay=False, dir_okay=True),
    help="Directory to write the platform-specific system prompts.",
)
@click.option(
    "--workflows-path",
    default=None,
    help=(
        "Local file path where the agent should cache workflows. "
        "Default: .agent/workflows_{version}.md"
    ),
)
@click.option(
    "--platform",
    "platforms",
    multiple=True,
    type=click.Choice(PLATFORMS),
    default=PLATFORMS,
    show_default=True,
    help="Which platform rules to generate. Repeat to select multiple.",
)
def export_agent_docs(
    base_url: str,
    api_version: str,
    output_dir: str,
    workflows_path: str | None,
    platforms: tuple[str, ...],
) -> None:
    """Generate platform-specific system prompts for API consumers."""
    base = base_url.rstrip("/")
    workflows_path = workflows_path or f".agent/workflows_{api_version}.md"
    fetch_url = f"{base}/{api_version}/agent-workflows"

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    env = _build_environment()
    context = {
        "base_url": base,
        "api_version": api_version,
        "workflows_path": workflows_path,
        "fetch_url": fetch_url,
    }

    written: list[Path] = []
    for platform in platforms:
        template = env.get_template(f"{platform}.md.j2")
        rendered = template.render(**context)
        target = output / f"{platform}-rules.md"
        target.write_text(rendered, encoding="utf-8")
        written.append(target)

    click.echo(f"Wrote {len(written)} file(s) to {output}:")
    for path in written:
        click.echo(f"  - {path}")
