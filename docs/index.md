# agent-grammar

**Test-gated AI agent workflow documentation for HTTP APIs.**

`agent-grammar` lets API developers attach machine-readable workflow
documentation to their existing `pytest` suite. When integration tests pass,
a `workflows.md` blueprint is auto-compiled and served at a versioned route so
that external developers' AI agents (Cursor, Claude, Copilot, Gemini) can
fetch it and generate accurate integration code — no hallucinated endpoints,
no missing parameter bindings.

!!! quote "Single source of truth"
    When business logic changes and tests are updated, the AI documentation
    re-compiles automatically. Only workflows whose tests pass are published.

## Why it exists

LLM coding assistants are excellent at producing code that *looks* right but
silently invents endpoints, swaps parameter names, or misses the order that
two API calls have to happen in. The fix isn't a longer prompt — it's a
machine-readable contract that the agent can fetch on demand.

!!! info "Not an MCP server"
    `agent-grammar` is aimed at making an agent a *better coder*, not a
    *self-sufficient* one. It never puts the agent in the request path —
    instead of exposing your endpoints as live tools the agent calls (the
    [`fastapi-mcp`](comparison.md) model), it hands the agent a test-gated
    contract so the integration code it writes is correct the first time. See
    [agent-grammar vs. fastapi-mcp](comparison.md) for the full comparison.

`agent-grammar` produces that contract directly from the tests you already
have:

1. Wrap a pytest test with `@workflow(...)` and use `AgentTestClient` instead
   of the framework's standard test client.
2. Run pytest. Every passing decorated test contributes one workflow to a
   compiled `workflows.md`.
3. Serve `workflows.md` from your API on a versioned route, or export per-
   platform rule files (`claude-rules.md`, `cursor-rules.md`, etc.) for your
   developer portal.

## What a workflow looks like

A decorated test:

```python
from agent_grammar import AgentTestClient, step_boundary, workflow
from app.main import app

client = AgentTestClient(app)

@workflow(
    name="VIP Fast Pass Booking",
    intent="Purchase a VIP ticket and reserve a ride with it.",
)
def test_vip_fast_pass_workflow():
    purchase = client.post("/v1/ticketing/purchase", json={"ticket_type": "VIP"})
    assert purchase.status_code == 200
    ticket_id = purchase.json()["ticket_uuid"]

    with step_boundary(domain="Client Logic", name="Compute reservation time"):
        reservation_time = "2026-06-03T12:00:00"

    reserve = client.post("/v1/rides/reserve", json={
        "ticket_uuid": ticket_id,
        "ride_name": "Titan Coaster",
        "reservation_time": reservation_time,
    })
    assert reserve.status_code == 200
```

Compiles to a blueprint with an ordered execution sequence plus the request
and response body that each step actually observed:

```markdown
## Workflow: VIP Fast Pass Booking
* **ID:** `vip_fast_pass_booking`
* **Intent:** Purchase a VIP ticket and reserve a ride with it.
* **Status:** Verified / Test-Gated

### 1. Ordered Execution Sequence
| Step | Domain / Boundary | Action | Description |
|---|---|---|---|
| 1 | `[Core Service]` | `POST /v1/ticketing/purchase` | ... |
| 2 | `[External/Mocked]` | `Client Logic Query` | Compute reservation time. ... |
| 3 | `[Core Service]` | `POST /v1/rides/reserve` | ... |

### 2. Observed Request & Response Payloads
#### Step 1 — `POST /v1/ticketing/purchase` → `200`
...the captured request/response bodies for each step, secrets redacted...
```

The data flow between steps is never hand-written: the agent reads the
observed payloads and matches field names and example values across steps
(for example, the `ticket_uuid` returned by step 1 reappears in step 3's
request body).

## Where to next

<div class="grid cards" markdown>

- :material-download: **[Installation](installation.md)** — Install the package and verify the pytest plugin loads.
- :material-rocket-launch: **[Walkthrough](walkthrough.md)** — Clone a real FastAPI demo and generate your first `workflows.md` in under 10 minutes.
- :material-cog: **[Configuration](configuration.md)** — All pytest options, CLI flags, and serving knobs.
- :material-book-open-page-variant: **[API Reference](api-reference.md)** — Generated reference for every public symbol.

</div>

## License

[MIT](https://github.com/dlfelps/agent-grammar/blob/main/LICENSE).
