"""Unit tests for AgentTestClient HTTP capture."""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from agent_grammar import AgentTestClient, workflow
from agent_grammar._models import HttpStep
from agent_grammar.testing.decorators import RECORDER_ATTR


async def _echo(request):
    body = await request.json()
    return JSONResponse({"echo": body}, status_code=201)


def _build_app() -> Starlette:
    return Starlette(routes=[Route("/echo", _echo, methods=["POST"])])


def test_client_records_http_step_when_workflow_active() -> None:
    client = AgentTestClient(_build_app())

    @workflow(name="EchoFlow", intent="exercise echo")
    def run() -> None:
        resp = client.post("/echo", json={"hello": "world"})
        assert resp.status_code == 201
        assert resp.json() == {"echo": {"hello": "world"}}

    run()
    recorder = getattr(run, RECORDER_ATTR)
    assert len(recorder.steps) == 1
    step = recorder.steps[0]
    assert isinstance(step, HttpStep)
    assert step.method == "POST"
    assert step.path == "/echo"
    assert step.status_code == 201
    assert step.request_json == {"hello": "world"}
    assert step.response_json == {"echo": {"hello": "world"}}


def test_client_no_capture_outside_workflow() -> None:
    client = AgentTestClient(_build_app())
    resp = client.post("/echo", json={"x": 1})
    assert resp.status_code == 201
    # No active recorder, no exception, no side effects.


def test_client_records_multiple_steps_in_order() -> None:
    client = AgentTestClient(_build_app())

    @workflow(name="MultiFlow", intent="x")
    def run() -> None:
        client.post("/echo", json={"n": 1})
        client.post("/echo", json={"n": 2})
        client.post("/echo", json={"n": 3})

    run()
    recorder = getattr(run, RECORDER_ATTR)
    assert len(recorder.steps) == 3
    assert [s.request_json["n"] for s in recorder.steps] == [1, 2, 3]
