"""Core data models for workflow recording and rendering."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Union


@dataclass
class HttpStep:
    method: str
    path: str
    request_json: Any | None
    status_code: int
    response_json: Any | None
    domain: str = "Core Service"


@dataclass
class BoundaryStep:
    domain: str
    name: str


Step = Union[HttpStep, BoundaryStep]


@dataclass
class Binding:
    source: str
    target: str


@dataclass
class WorkflowRecord:
    name: str
    slug: str
    intent: str
    bindings: list[Binding] = field(default_factory=list)
    steps: list[Step] = field(default_factory=list)


_SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    lowered = name.strip().lower()
    collapsed = _SLUG_NON_ALNUM.sub("_", lowered)
    return collapsed.strip("_")
