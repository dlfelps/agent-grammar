"""Workflow decorator and step boundary context manager."""

from __future__ import annotations

import asyncio
import functools
from contextlib import contextmanager
from typing import Any, Callable, Iterator

from agent_grammar._context import (
    WorkflowRecorder,
    get_active_recorder,
    reset_recorder,
    set_active_recorder,
)
from agent_grammar._models import Binding, BoundaryStep

RECORDER_ATTR = "_agent_grammar_recorder"


def _normalize_bindings(
    raw: list[dict[str, str] | Binding] | None,
) -> list[Binding]:
    if not raw:
        return []
    out: list[Binding] = []
    for item in raw:
        if isinstance(item, Binding):
            out.append(item)
        else:
            out.append(Binding(source=item["source"], target=item["target"]))
    return out


def workflow(
    *,
    name: str,
    intent: str,
    bindings: list[dict[str, str] | Binding] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorate a pytest test function to record its HTTP/boundary steps.

    The recorder is stashed on the wrapper as ``_agent_grammar_recorder`` so the
    pytest plugin can collect it after the test passes.
    """

    normalized = _normalize_bindings(bindings)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        recorder = WorkflowRecorder(name=name, intent=intent, bindings=normalized)

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                token = set_active_recorder(recorder)
                try:
                    result = await func(*args, **kwargs)
                    recorder.mark_complete()
                    return result
                finally:
                    reset_recorder(token)

            setattr(async_wrapper, RECORDER_ATTR, recorder)
            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            token = set_active_recorder(recorder)
            try:
                result = func(*args, **kwargs)
                recorder.mark_complete()
                return result
            finally:
                reset_recorder(token)

        setattr(sync_wrapper, RECORDER_ATTR, recorder)
        return sync_wrapper

    return decorator


@contextmanager
def step_boundary(*, domain: str, name: str) -> Iterator[None]:
    """Mark a non-HTTP step (e.g. database query, external service)."""
    recorder = get_active_recorder()
    if recorder is not None:
        recorder.add_boundary_step(BoundaryStep(domain=domain, name=name))
    yield
