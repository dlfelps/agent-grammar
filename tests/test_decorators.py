"""Unit tests for the @workflow decorator and step_boundary context manager."""

from __future__ import annotations

import asyncio

import pytest

from agent_grammar import step_boundary, workflow
from agent_grammar._context import get_active_recorder
from agent_grammar.testing.decorators import RECORDER_ATTR


def test_workflow_attaches_recorder_to_wrapper() -> None:
    @workflow(name="Demo", intent="testing")
    def demo() -> None:
        pass

    recorder = getattr(demo, RECORDER_ATTR)
    assert recorder.name == "Demo"
    assert recorder.intent == "testing"
    assert recorder.complete is False


def test_workflow_marks_complete_on_clean_run() -> None:
    @workflow(name="Demo", intent="x")
    def demo() -> None:
        return None

    demo()
    recorder = getattr(demo, RECORDER_ATTR)
    assert recorder.complete is True


def test_workflow_does_not_mark_complete_on_exception() -> None:
    @workflow(name="Demo", intent="x")
    def demo() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        demo()
    recorder = getattr(demo, RECORDER_ATTR)
    assert recorder.complete is False


def test_workflow_resets_contextvar_after_run() -> None:
    @workflow(name="Demo", intent="x")
    def demo() -> None:
        assert get_active_recorder() is not None

    assert get_active_recorder() is None
    demo()
    assert get_active_recorder() is None


def test_step_boundary_no_op_outside_workflow() -> None:
    with step_boundary(domain="Database", name="some query"):
        pass


def test_step_boundary_records_when_active() -> None:
    @workflow(name="Demo", intent="x")
    def demo() -> None:
        with step_boundary(domain="Database", name="query A"):
            pass
        with step_boundary(domain="Email", name="send confirmation"):
            pass

    demo()
    recorder = getattr(demo, RECORDER_ATTR)
    assert len(recorder.steps) == 2
    assert recorder.steps[0].domain == "Database"
    assert recorder.steps[1].name == "send confirmation"


def test_workflow_supports_async() -> None:
    @workflow(name="AsyncDemo", intent="x")
    async def demo() -> int:
        with step_boundary(domain="Async", name="await something"):
            pass
        return 42

    result = asyncio.run(demo())
    assert result == 42
    recorder = getattr(demo, RECORDER_ATTR)
    assert recorder.complete is True
    assert len(recorder.steps) == 1


def test_workflow_normalizes_dict_bindings() -> None:
    @workflow(
        name="Demo",
        intent="x",
        bindings=[{"source": "Step 1.foo", "target": "Step 2.bar"}],
    )
    def demo() -> None:
        pass

    recorder = getattr(demo, RECORDER_ATTR)
    assert recorder.bindings[0].source == "Step 1.foo"
    assert recorder.bindings[0].target == "Step 2.bar"
