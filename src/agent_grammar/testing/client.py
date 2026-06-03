"""AgentTestClient: a TestClient subclass that records HTTP traffic."""

from __future__ import annotations

from typing import Any

from starlette.testclient import TestClient

from agent_grammar._context import get_active_recorder
from agent_grammar._models import HttpStep


def _safe_response_json(response: Any) -> Any | None:
    try:
        return response.json()
    except (ValueError, Exception):
        return None


class AgentTestClient(TestClient):
    """Drop-in replacement for ``starlette.testclient.TestClient``.

    When invoked inside a ``@workflow``-decorated test, each request is
    captured as an ``HttpStep`` and appended to the active recorder.
    """

    def request(  # type: ignore[override]
        self,
        method: str,
        url: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        response = super().request(method, url, *args, **kwargs)
        recorder = get_active_recorder()
        if recorder is not None:
            recorder.add_http_step(
                HttpStep(
                    method=method.upper(),
                    path=str(url),
                    request_json=kwargs.get("json"),
                    status_code=response.status_code,
                    response_json=_safe_response_json(response),
                )
            )
        return response
