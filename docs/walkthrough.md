# Walkthrough

In this walkthrough you'll take an existing FastAPI demo project,
[dlfelps/roller-coaster](https://github.com/dlfelps/roller-coaster) — a small
"Theme Park Tycoon Manager" API with three integration tests — and adapt it
so that running `pytest` produces a `workflows.md` blueprint describing each
multi-step workflow.

You should be able to finish in under ten minutes.

## What you'll build

The roller-coaster project ships with three integration tests, each
exercising a multi-step business flow:

1. **VIP Fast Pass Booking** — Buy a VIP ticket, then reserve a ride with it.
2. **Weather-Triggered Evacuation** — A weather alert triggers park-wide
   alarms and then issues mass refunds.
3. **Mascot Security Dispatch** — Look up a mascot's zone, compute a path,
   then dispatch security.

You'll decorate each test with `@workflow(...)`, swap its HTTP client for
`AgentTestClient`, and add `step_boundary` blocks around the non-HTTP logic
(client-side calculations, simulated external alerts). When the tests pass,
all three workflows land in `assets/workflows.md`.

## 1. Clone the demo

```bash
git clone https://github.com/dlfelps/roller-coaster.git
cd roller-coaster
```

## 2. Install dependencies

The demo's own dependencies plus `agent-grammar`:

```bash
pip install -r requirements.txt
pip install agent-grammar
```

## 3. Tour the project

```
roller-coaster/
├── app/
│   └── main.py            # FastAPI app, 6 endpoints across ticketing,
│                          # rides, alarms, refunds, mascots, security.
├── tests/
│   └── test_workflows.py  # Three multi-step integration tests.
└── requirements.txt
```

Run the suite as-is to confirm it passes before you change anything:

```bash
pytest
```

You should see three passing tests.

## 4. Adapt the tests

Open `tests/test_workflows.py` and replace its contents with the version
below. Three things change:

- **Import** `AgentTestClient`, `step_boundary`, and `workflow` from
  `agent_grammar`. The standard `fastapi.testclient.TestClient` becomes
  `AgentTestClient`.
- **Decorate** each test with `@workflow(...)`, giving it a display name,
  an intent, and the parameter bindings that an AI agent will need to wire
  its requests together.
- **Mark non-HTTP steps** with `step_boundary(...)` so they show up in the
  blueprint as `[External/Mocked]`-style rows the agent has to fill in.

```python title="tests/test_workflows.py"
from datetime import datetime, timedelta

from agent_grammar import AgentTestClient, step_boundary, workflow
from app.main import app

client = AgentTestClient(app)


@workflow(
    name="VIP Fast Pass Booking",
    intent="Purchase a VIP ticket and reserve a ride with the acquired ticket UUID.",
    bindings=[
        {"source": "Step 1.response.ticket_uuid",
         "target": "Step 3.body.ticket_uuid"},
        {"source": "Step 2.computed_reservation_time",
         "target": "Step 3.body.reservation_time"},
    ],
)
def test_vip_fast_pass_workflow():
    """Buy a VIP pass and immediately book a ride 15 minutes out."""
    # Step 1: Buy the pass
    purchase_resp = client.post(
        "/v1/ticketing/purchase", json={"ticket_type": "VIP"}
    )
    assert purchase_resp.status_code == 200
    ticket_id = purchase_resp.json()["ticket_uuid"]

    # Step 2: Compute reservation time client-side
    with step_boundary(domain="Client Logic",
                       name="Compute reservation time (now + 15 min, ISO 8601)"):
        future_time = (datetime.utcnow() + timedelta(minutes=15)).isoformat()

    # Step 3: Book the ride
    reserve_resp = client.post(
        "/v1/rides/reserve",
        json={
            "ticket_uuid": ticket_id,
            "ride_name": "Titan Coaster",
            "reservation_time": future_time,
        },
    )
    assert reserve_resp.status_code == 200
    assert reserve_resp.json()["status"] == "reserved"


@workflow(
    name="Weather-Triggered Evacuation",
    intent="Detect a severe weather event, raise park-wide alarms, and issue mass refunds.",
    bindings=[
        {"source": "Step 1.weather_reason",
         "target": "Step 2.body.reason"},
        {"source": "Step 1.weather_reason",
         "target": "Step 3.body.reason"},
    ],
)
def test_weather_evacuation_workflow():
    """Trigger park alarms in response to a weather event, then refund tickets."""
    # Step 1: Pretend an external weather API returned an alert
    with step_boundary(domain="External Weather API",
                       name="Receive severe-weather alert payload"):
        weather_alert_reason = "Severe Lightning Strike"

    # Step 2: Raise park-wide alarms
    alarm_resp = client.post(
        "/v1/park/alarms/trigger",
        json={"reason": weather_alert_reason, "zone": "ALL"},
    )
    assert alarm_resp.status_code == 200
    assert alarm_resp.json()["alarm_status"] == "ACTIVE"

    # Step 3: Issue mass refunds (auth override required)
    refund_resp = client.post(
        "/v1/ticketing/mass-refund",
        json={"reason": weather_alert_reason, "auth_override": True},
    )
    assert refund_resp.status_code == 200
    assert refund_resp.json()["refunded_count"] > 0


@workflow(
    name="Mascot Security Dispatch",
    intent="Look up a mascot's zone, compute a path to it, and dispatch security.",
    bindings=[
        {"source": "Step 1.response.zone_id",
         "target": "Step 3.body.target_zone"},
        {"source": "Step 2.computed_path",
         "target": "Step 3.body.path_array"},
    ],
)
def test_mascot_dispatch_workflow():
    """Locate a mascot, compute a path, and send security along it."""
    # Step 1: Find the mascot
    mascot_resp = client.get("/v1/mascots/T-Rex/location")
    assert mascot_resp.status_code == 200
    target_zone = mascot_resp.json()["zone_id"]

    # Step 2: Compute a path client-side
    with step_boundary(domain="Pathfinding",
                       name="Compute route from Entrance to mascot zone"):
        calculated_path = ["Entrance", "Main Street", "Zone-A", target_zone]

    # Step 3: Dispatch security
    dispatch_resp = client.post(
        "/v1/security/dispatch",
        json={"target_zone": target_zone, "path_array": calculated_path},
    )
    assert dispatch_resp.status_code == 200
    assert dispatch_resp.json()["status"] == "dispatched"
```

!!! tip "What changed and why"
    - `AgentTestClient` wraps Starlette's `TestClient`. Every request it
      makes during a `@workflow`-decorated test is recorded as a step.
    - `step_boundary` doesn't run any HTTP, it just inserts a non-HTTP row
      into the workflow. Use it for client-side calculations, mocked
      external services, queued work — anything an integrator will need to
      implement on their side.
    - `bindings` declare data-flow contracts in the form
      `"Step N.<location>" → "Step M.<location>"`. The numbers refer to the
      step's position in the workflow, counting both HTTP and boundary
      steps. These bindings are what stop an agent from inventing parameter
      names or losing track of which value flows where.

## 5. Generate the workflows blueprint

```bash
pytest --agent-grammar-output=assets/workflows.md
```

All three tests should still pass. After the session, the plugin writes
`assets/workflows.md`. Open it and you'll see three sections — one per
workflow — each with:

- A workflow ID (the slugified name)
- The declared intent
- An "Ordered Execution Sequence" table listing every HTTP and boundary step
- A "Precise Parameter Bindings" table derived from the `bindings=[...]`
  argument

!!! warning "Test-gated guarantee"
    If any decorated test fails, that workflow is excluded from
    `workflows.md`. The output never gets out of sync with what the tests
    actually verify.

## 6. (Optional) Serve the blueprint from your API

Mount `GrammarRouter` so the compiled markdown is available on a versioned
route — that's the URL your customers' agents will fetch.

```python title="app/main.py (additions)"
from agent_grammar.serve.fastapi import AgentTelemetryMiddleware, GrammarRouter


def log_agent_metric(workflow_id: str) -> None:
    print(f"METRIC: agent-driven request for workflow {workflow_id}")


app.add_middleware(AgentTelemetryMiddleware, on_detect=log_agent_metric)
app.include_router(
    GrammarRouter(filepath="assets/workflows.md"),
    prefix="/v1/agent-workflows",
)
```

Run the server:

```bash
uvicorn app.main:app --reload
```

`GET http://localhost:8000/v1/agent-workflows` now serves the markdown.
`AgentTelemetryMiddleware` watches for incoming requests carrying
`X-Agent-Grammar-Workflow: <workflow-id>` and calls your callback with the
ID on every successful (2xx) response — handy for tracking which workflows
agents actually use.

## 7. (Optional) Export per-platform rule files

Generate ready-to-paste system prompts for the major coding assistants:

```bash
agent-grammar export-agent-docs \
    --base-url https://api.example.com \
    --api-version v1
```

You'll find rule files under `agent-docs/`:

```
agent-docs/
├── claude-rules.md
├── cursor-rules.md
├── copilot-rules.md
└── gemini-rules.md
```

Drop these into your developer portal so an agent fetching them gets the
right base URL, version, and instruction to consult `workflows.md` before
generating integration code.

## Next steps

- Read the [Configuration](configuration.md) page for every pytest option,
  `GrammarRouter` parameter, and CLI flag.
- See the [API Reference](api-reference.md) for the full Python surface.
- Add `@workflow` to one of *your* own integration tests and watch its
  workflow appear in the blueprint.
