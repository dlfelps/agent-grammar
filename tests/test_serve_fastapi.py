"""Tests for GrammarRouter and AgentTelemetryMiddleware."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from agent_grammar.serve.fastapi import (
    MARKDOWN_MEDIA_TYPE,
    AgentTelemetryMiddleware,
    GrammarRouter,
)


def _write_sample_markdown(tmp_path: Path) -> Path:
    p = tmp_path / "workflows.md"
    p.write_text("# Sample Workflows\n\nhello world\n", encoding="utf-8")
    return p


def test_grammar_router_serves_markdown(tmp_path: Path) -> None:
    md = _write_sample_markdown(tmp_path)
    app = FastAPI()
    app.include_router(GrammarRouter(md), prefix="/v1/agent-workflows")

    client = TestClient(app)
    resp = client.get("/v1/agent-workflows/")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    assert resp.text == "# Sample Workflows\n\nhello world\n"


def test_grammar_router_serves_at_bare_prefix(tmp_path: Path) -> None:
    md = _write_sample_markdown(tmp_path)
    app = FastAPI()
    app.include_router(GrammarRouter(md), prefix="/v1/agent-workflows")

    client = TestClient(app)
    resp = client.get("/v1/agent-workflows")
    assert resp.status_code == 200
    assert resp.text == "# Sample Workflows\n\nhello world\n"


def test_grammar_router_caches_content_by_default(tmp_path: Path) -> None:
    md = _write_sample_markdown(tmp_path)
    app = FastAPI()
    app.include_router(GrammarRouter(md), prefix="/v1/agent-workflows")
    client = TestClient(app)

    md.write_text("# Changed\n", encoding="utf-8")
    resp = client.get("/v1/agent-workflows/")
    # Cached at construction time — sees the original content.
    assert "Sample Workflows" in resp.text


def test_grammar_router_reload_mode_picks_up_changes(tmp_path: Path) -> None:
    md = _write_sample_markdown(tmp_path)
    app = FastAPI()
    app.include_router(
        GrammarRouter(md, reload=True), prefix="/v1/agent-workflows"
    )
    client = TestClient(app)

    md.write_text("# Changed\n", encoding="utf-8")
    resp = client.get("/v1/agent-workflows/")
    assert "Changed" in resp.text


def test_grammar_router_raises_when_file_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        GrammarRouter(tmp_path / "nope.md")


def test_grammar_router_media_type_constant() -> None:
    assert MARKDOWN_MEDIA_TYPE == "text/markdown; charset=utf-8"


def test_telemetry_middleware_invokes_callback_on_2xx() -> None:
    calls: list[str] = []

    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict:
        return {"ok": True}

    app.add_middleware(
        AgentTelemetryMiddleware, on_detect=lambda wid: calls.append(wid)
    )
    client = TestClient(app)
    resp = client.get(
        "/ping", headers={"X-Agent-Grammar-Workflow": "demo_flow"}
    )
    assert resp.status_code == 200
    assert calls == ["demo_flow"]


def test_telemetry_middleware_skips_when_header_missing() -> None:
    calls: list[str] = []
    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict:
        return {"ok": True}

    app.add_middleware(
        AgentTelemetryMiddleware, on_detect=lambda wid: calls.append(wid)
    )
    client = TestClient(app)
    resp = client.get("/ping")
    assert resp.status_code == 200
    assert calls == []


def test_telemetry_middleware_skips_on_error_response() -> None:
    calls: list[str] = []
    app = FastAPI()

    @app.get("/boom")
    def boom() -> dict:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail="nope")

    app.add_middleware(
        AgentTelemetryMiddleware, on_detect=lambda wid: calls.append(wid)
    )
    client = TestClient(app)
    resp = client.get(
        "/boom", headers={"X-Agent-Grammar-Workflow": "demo_flow"}
    )
    assert resp.status_code == 500
    assert calls == []


def test_telemetry_middleware_swallows_callback_errors() -> None:
    def boom(_: str) -> None:
        raise RuntimeError("intentional")

    app = FastAPI()

    @app.get("/ping")
    def ping() -> dict:
        return {"ok": True}

    app.add_middleware(AgentTelemetryMiddleware, on_detect=boom)
    client = TestClient(app)
    resp = client.get(
        "/ping", headers={"X-Agent-Grammar-Workflow": "demo_flow"}
    )
    # Telemetry failure must not break business traffic.
    assert resp.status_code == 200
