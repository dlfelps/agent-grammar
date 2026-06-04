"""ContextVar-based recorder lifecycle for the workflow capture pipeline."""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from agent_grammar._models import (
    BoundaryStep,
    HttpStep,
    WorkflowRecord,
    slugify,
)


class WorkflowRecorder:
    """Mutable builder collecting steps as a decorated test runs."""

    def __init__(
        self,
        name: str,
        intent: str,
    ) -> None:
        self.name = name
        self.intent = intent
        self.steps: list[HttpStep | BoundaryStep] = []
        self.complete: bool = False

    def add_http_step(self, step: HttpStep) -> None:
        self.steps.append(step)

    def add_boundary_step(self, step: BoundaryStep) -> None:
        self.steps.append(step)

    def mark_complete(self) -> None:
        self.complete = True

    def build(self) -> WorkflowRecord:
        return WorkflowRecord(
            name=self.name,
            slug=slugify(self.name),
            intent=self.intent,
            steps=list(self.steps),
        )


_current_recorder: ContextVar[WorkflowRecorder | None] = ContextVar(
    "agent_grammar_recorder", default=None
)


def get_active_recorder() -> WorkflowRecorder | None:
    return _current_recorder.get()


def set_active_recorder(recorder: WorkflowRecorder | None) -> Any:
    return _current_recorder.set(recorder)


def reset_recorder(token: Any) -> None:
    _current_recorder.reset(token)
