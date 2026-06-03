"""Tests for the ``agent-grammar export-agent-docs`` CLI."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from agent_grammar.cli.main import cli


def test_export_generates_all_platforms(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "export-agent-docs",
            "--base-url",
            "https://api.production.com",
            "--api-version",
            "v1",
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output

    for platform in ("cursor", "claude", "copilot", "gemini"):
        target = tmp_path / f"{platform}-rules.md"
        assert target.exists(), f"missing {target}"
        text = target.read_text(encoding="utf-8")
        assert "https://api.production.com/v1/agent-workflows" in text
        assert ".agent/workflows_v1.md" in text
        assert "X-Agent-Grammar-Workflow" in text


def test_export_respects_custom_workflows_path(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "export-agent-docs",
            "--base-url",
            "https://api.example.com",
            "--api-version",
            "v2",
            "--output-dir",
            str(tmp_path),
            "--workflows-path",
            "docs/agent.md",
        ],
    )
    assert result.exit_code == 0, result.output
    cursor = (tmp_path / "cursor-rules.md").read_text(encoding="utf-8")
    assert "docs/agent.md" in cursor
    assert "https://api.example.com/v2/agent-workflows" in cursor


def test_export_single_platform(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "export-agent-docs",
            "--base-url",
            "https://api.example.com",
            "--output-dir",
            str(tmp_path),
            "--platform",
            "claude",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / "claude-rules.md").exists()
    assert not (tmp_path / "cursor-rules.md").exists()


def test_export_strips_trailing_slash_from_base_url(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "export-agent-docs",
            "--base-url",
            "https://api.example.com/",
            "--output-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0
    cursor = (tmp_path / "cursor-rules.md").read_text(encoding="utf-8")
    assert "https://api.example.com/v1/agent-workflows" in cursor
    assert "https://api.example.com//v1" not in cursor


def test_cli_version_flag() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "agent-grammar" in result.output
