"""Pytest plugin that aggregates passing workflows and writes ``workflows.md``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agent_grammar.testing.decorators import RECORDER_ATTR
from agent_grammar.testing.registry import WorkflowRegistry
from agent_grammar.testing.renderer import MarkdownRenderer

DEFAULT_OUTPUT = "assets/workflows.md"
REGISTRY_ATTR = "_agent_grammar_registry"


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("agent-grammar")
    group.addoption(
        "--agent-grammar-output",
        action="store",
        dest="agent_grammar_output",
        default=None,
        help="Path to write the compiled workflows.md (default: assets/workflows.md).",
    )
    group.addoption(
        "--agent-grammar-disable",
        action="store_true",
        dest="agent_grammar_disable",
        default=False,
        help="Skip writing the compiled workflows.md file.",
    )
    parser.addini(
        "agent_grammar_output",
        help="Path to write the compiled workflows.md (default: assets/workflows.md).",
        default=DEFAULT_OUTPUT,
    )


def pytest_configure(config: pytest.Config) -> None:
    setattr(config, REGISTRY_ATTR, WorkflowRegistry())


def _get_recorder(item: pytest.Item) -> Any:
    obj = getattr(item, "obj", None)
    if obj is None:
        return None
    return getattr(obj, RECORDER_ATTR, None)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(
    item: pytest.Item, call: pytest.CallInfo[None]
) -> Any:
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or report.outcome != "passed":
        return
    recorder = _get_recorder(item)
    if recorder is None or not recorder.complete:
        return
    registry: WorkflowRegistry | None = getattr(
        item.config, REGISTRY_ATTR, None
    )
    if registry is None:
        return
    registry.add(recorder.build())


def _resolve_output_path(config: pytest.Config) -> Path:
    cli_value = config.getoption("agent_grammar_output", default=None)
    if cli_value:
        return Path(cli_value)
    ini_value = config.getini("agent_grammar_output") or DEFAULT_OUTPUT
    return Path(ini_value)


def pytest_sessionfinish(
    session: pytest.Session, exitstatus: int
) -> None:
    config = session.config
    if config.getoption("agent_grammar_disable", default=False):
        return
    registry: WorkflowRegistry | None = getattr(
        config, REGISTRY_ATTR, None
    )
    if registry is None or len(registry) == 0:
        return
    output = _resolve_output_path(config)
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = MarkdownRenderer().render(registry.records)
    output.write_text(rendered, encoding="utf-8")
    reporter = config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        reporter.write_line(
            f"[agent-grammar] wrote {len(registry)} workflow(s) to {output}"
        )
