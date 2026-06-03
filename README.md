# agent-grammar

**Test-gated AI agent workflow documentation for HTTP APIs.**

📖 **Full documentation:** <https://dlfelps.github.io/agent-grammar/>

`agent-grammar` lets API developers attach machine-readable workflow
documentation to their existing `pytest` suite. When integration tests pass,
a `workflows.md` blueprint is auto-compiled and served at a versioned route so
that external developers' AI agents (Cursor, Claude, Copilot, Gemini) can
fetch it and generate accurate integration code — no hallucinated endpoints,
no missing parameter bindings.

> Single source of truth: when business logic changes and tests are updated,
> the AI documentation re-compiles automatically.

## Install

```bash
pip install agent-grammar          # core (pytest + serve via Starlette)
pip install "agent-grammar[fastapi]"  # adds FastAPI for serving
```

The pytest plugin is registered through the `pytest11` entry point and is
discovered automatically once the package is installed — no `conftest.py`
change required.

## Quick Start

### 1. Annotate an integration test

```python
from agent_grammar import AgentTestClient, step_boundary, workflow
from app.main import app

client = AgentTestClient(app)

@workflow(
    name="Material Onboarding Lifecycle",
    intent="Secure a token, query the local DB for a zone, and register an asset.",
    bindings=[
        {"source": "Step 1.response.access_token", "target": "Step 3.headers.Authorization"},
        {"source": "Step 2.mocked_db_result",      "target": "Step 3.body.assigned_zone"},
    ],
)
def test_compile_material_onboarding():
    auth = client.post("/v1/auth/token", json={"seed": "dev-token"})
    assert auth.status_code == 200
    token = auth.json()["access_token"]

    with step_boundary(domain="Database", name="Query PostgreSQL for Zone UUID"):
        zone_id = "mocked-uuid-from-db-query"

    resp = client.post(
        "/v1/materials",
        json={"sku": "MAT-9901", "assigned_zone": zone_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
```

### 2. Run the test suite

```bash
pytest --agent-grammar-output=assets/workflows.md
```

When the test passes, `assets/workflows.md` is compiled. Failing tests are
excluded — that's the "Test-Gated" guarantee.

### 3. Serve the compiled markdown

```python
from fastapi import FastAPI
from agent_grammar.serve.fastapi import AgentTelemetryMiddleware, GrammarRouter

app = FastAPI(title="Core Engine API - v1")

def log_agent_metric(workflow_id: str) -> None:
    print(f"METRIC: agent-driven request for workflow {workflow_id}")

app.add_middleware(AgentTelemetryMiddleware, on_detect=log_agent_metric)
app.include_router(
    GrammarRouter(filepath="assets/workflows.md"),
    prefix="/v1/agent-workflows",
)
```

### 4. Publish system prompts for external developers

```bash
agent-grammar export-agent-docs \
    --base-url https://api.production.com \
    --api-version v1
```

Writes `./agent-docs/{cursor,claude,copilot,gemini}-rules.md` ready for the
API host's developer portal.

## Documentation

The full documentation site at <https://dlfelps.github.io/agent-grammar/>
covers:

- **[Installation](https://dlfelps.github.io/agent-grammar/installation/)** — Python versions, install variants, and verification.
- **[Walkthrough](https://dlfelps.github.io/agent-grammar/walkthrough/)** — Clone the [`dlfelps/roller-coaster`](https://github.com/dlfelps/roller-coaster) FastAPI demo, decorate its three tests, and generate `workflows.md` end-to-end in under 10 minutes.
- **[Configuration](https://dlfelps.github.io/agent-grammar/configuration/)** — Every pytest flag, `GrammarRouter` argument, and CLI option.
- **[API Reference](https://dlfelps.github.io/agent-grammar/api-reference/)** — Generated from the in-package docstrings.

## Configuration

| Option | Where | Default |
|---|---|---|
| `--agent-grammar-output` | pytest CLI | `assets/workflows.md` |
| `agent_grammar_output`   | `pyproject.toml` `[tool.pytest.ini_options]` | `assets/workflows.md` |
| `--agent-grammar-disable` | pytest CLI | off |

## License

MIT
