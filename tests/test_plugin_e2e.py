"""End-to-end pytest plugin tests using the ``pytester`` fixture.

Each test spawns a child ``pytest`` process so the plugin is exercised in
realistic conditions, isolated from the host run.
"""

from __future__ import annotations

import pytest

SAMPLE_TEST = '''
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from agent_grammar import AgentTestClient, step_boundary, workflow


async def issue_token(request):
    payload = await request.json()
    assert payload["seed"]
    return JSONResponse({"access_token": "sample-token-abc123"})


async def register_material(request):
    payload = await request.json()
    assert request.headers["authorization"].startswith("Bearer ")
    return JSONResponse({"id": "mat-001", **payload}, status_code=201)


app = Starlette(routes=[
    Route("/v1/auth/token", issue_token, methods=["POST"]),
    Route("/v1/materials", register_material, methods=["POST"]),
])
client = AgentTestClient(app)


@workflow(
    name="Material Onboarding Lifecycle",
    intent="Secure an identity token, query the local database for a zone, and register an asset.",
)
def test_compile_material_onboarding():
    auth_resp = client.post("/v1/auth/token", json={"seed": "dev-token"})
    assert auth_resp.status_code == 200
    token = auth_resp.json()["access_token"]

    with step_boundary(domain="Database", name="Query PostgreSQL for Zone UUID"):
        zone_id = "mocked-uuid-from-db-query"

    payload = {"sku": "MAT-9901", "assigned_zone": zone_id}
    material_resp = client.post(
        "/v1/materials",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert material_resp.status_code == 201
'''


def test_plugin_writes_workflows_md(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(test_sample=SAMPLE_TEST)
    result = pytester.runpytest("--agent-grammar-output=workflows.md")
    result.assert_outcomes(passed=1)

    output = pytester.path / "workflows.md"
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "## Workflow: Material Onboarding Lifecycle" in content
    assert "`material_onboarding_lifecycle`" in content
    assert "`POST /v1/auth/token`" in content
    assert "`[External/Mocked]`" in content
    assert "`POST /v1/materials`" in content


def test_plugin_excludes_failing_workflows(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_mixed=(
            "from agent_grammar import AgentTestClient, workflow\n"
            "from starlette.applications import Starlette\n"
            "from starlette.responses import JSONResponse\n"
            "from starlette.routing import Route\n"
            "\n"
            "async def ok(request):\n"
            "    return JSONResponse({'ok': True})\n"
            "\n"
            "app = Starlette(routes=[Route('/ok', ok, methods=['GET'])])\n"
            "client = AgentTestClient(app)\n"
            "\n"
            "@workflow(name='Passing Flow', intent='works')\n"
            "def test_pass():\n"
            "    assert client.get('/ok').status_code == 200\n"
            "\n"
            "@workflow(name='Failing Flow', intent='fails')\n"
            "def test_fail():\n"
            "    client.get('/ok')\n"
            "    assert False, 'intentional failure'\n"
        )
    )
    result = pytester.runpytest("--agent-grammar-output=workflows.md")
    result.assert_outcomes(passed=1, failed=1)

    output = pytester.path / "workflows.md"
    assert output.exists()
    content = output.read_text(encoding="utf-8")
    assert "Passing Flow" in content
    assert "Failing Flow" not in content


def test_plugin_disable_flag_skips_output(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_skip=(
            "from agent_grammar import workflow\n"
            "@workflow(name='No-op', intent='x')\n"
            "def test_noop():\n"
            "    assert True\n"
        )
    )
    result = pytester.runpytest(
        "--agent-grammar-output=workflows.md", "--agent-grammar-disable"
    )
    result.assert_outcomes(passed=1)
    assert not (pytester.path / "workflows.md").exists()


def test_plugin_no_output_when_no_workflows(pytester: pytest.Pytester) -> None:
    pytester.makepyfile(
        test_plain=(
            "def test_plain():\n"
            "    assert 1 + 1 == 2\n"
        )
    )
    result = pytester.runpytest("--agent-grammar-output=workflows.md")
    result.assert_outcomes(passed=1)
    assert not (pytester.path / "workflows.md").exists()
