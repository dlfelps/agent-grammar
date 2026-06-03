"""Session-scoped registry of workflow records collected during a test run."""

from __future__ import annotations

import warnings

from agent_grammar._models import WorkflowRecord


class WorkflowRegistry:
    """Collects ``WorkflowRecord`` instances from passing tests."""

    def __init__(self) -> None:
        self._records: dict[str, WorkflowRecord] = {}

    def add(self, record: WorkflowRecord) -> None:
        if record.slug in self._records:
            warnings.warn(
                f"Duplicate workflow slug '{record.slug}'; overwriting previous record.",
                stacklevel=2,
            )
        self._records[record.slug] = record

    @property
    def records(self) -> list[WorkflowRecord]:
        return list(self._records.values())

    def __len__(self) -> int:
        return len(self._records)
