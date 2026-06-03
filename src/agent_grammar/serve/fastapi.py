"""FastAPI/Starlette helpers: GrammarRouter and AgentTelemetryMiddleware."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

logger = logging.getLogger("agent_grammar.serve")

TELEMETRY_HEADER = "X-Agent-Grammar-Workflow"
MARKDOWN_MEDIA_TYPE = "text/markdown; charset=utf-8"


def GrammarRouter(
    filepath: str | Path,
    *,
    reload: bool = False,
):
    """Return a FastAPI/Starlette router that serves the compiled markdown.

    Args:
        filepath: Path to the compiled workflows.md asset.
        reload: If True, re-read the file on every request (dev mode).
                If False, cache contents in memory at construction time.

    Raises:
        FileNotFoundError: If ``filepath`` does not exist at construction time.
        ImportError: If FastAPI is not installed.
    """
    try:
        from fastapi import APIRouter
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "GrammarRouter requires FastAPI. Install with "
            "`pip install agent-grammar[fastapi]`."
        ) from exc

    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(
            f"GrammarRouter: workflows file not found at {path!s}. "
            "Did you run pytest to compile it?"
        )

    cached_content: str | None = None
    if not reload:
        cached_content = path.read_text(encoding="utf-8")

    router = APIRouter()

    @router.get("", include_in_schema=False)
    @router.get("/", include_in_schema=False)
    def _serve_workflows() -> PlainTextResponse:
        if reload:
            content = path.read_text(encoding="utf-8")
        else:
            assert cached_content is not None
            content = cached_content
        return PlainTextResponse(
            content=content, media_type=MARKDOWN_MEDIA_TYPE
        )

    return router


class AgentTelemetryMiddleware(BaseHTTPMiddleware):
    """Detect requests bearing ``X-Agent-Grammar-Workflow`` and report them.

    The middleware never raises from the telemetry callback — failures are
    logged and swallowed so business traffic is unaffected.
    """

    def __init__(
        self,
        app,
        on_detect: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(app)
        self.on_detect = on_detect

    async def dispatch(self, request: Request, call_next) -> Response:
        workflow_id = request.headers.get(TELEMETRY_HEADER)
        response = await call_next(request)
        if (
            workflow_id
            and self.on_detect is not None
            and 200 <= response.status_code < 300
        ):
            try:
                self.on_detect(workflow_id)
            except Exception:
                logger.exception(
                    "agent-grammar telemetry callback raised; ignoring."
                )
        return response
