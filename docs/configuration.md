# Configuration

Reference for every option exposed by the pytest plugin, the CLI, and the
serving helpers.

## pytest plugin

The plugin is registered automatically through the `pytest11` entry point in
`pyproject.toml`. It contributes two CLI flags and one ini option.

### CLI flags

| Flag | Default | Description |
|---|---|---|
| `--agent-grammar-output PATH` | falls back to ini, then `assets/workflows.md` | Path to write the compiled `workflows.md` after the session. |
| `--agent-grammar-disable` | off | Skip writing `workflows.md` entirely. The registry still collects workflows; nothing is persisted. |

### `pyproject.toml`

```toml
[tool.pytest.ini_options]
agent_grammar_output = "assets/workflows.md"
```

The CLI flag wins over the ini value. If neither is set, the default is
`assets/workflows.md` (resolved from the pytest invocation's working
directory).

### Behavior

- A workflow is recorded only if its test reaches `passed` outcome in the
  `call` phase. Errors during setup or teardown disqualify it.
- The plugin creates the output file's parent directory if it doesn't exist.
- After the session, the plugin writes a single line to the terminal
  reporter: `[agent-grammar] wrote N workflow(s) to <path>`.

## Decorator API

### `@workflow(...)`

| Argument | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | yes | Display name. Slugified into the workflow ID (`"VIP Fast Pass"` → `vip_fast_pass`). |
| `intent` | `str` | yes | One-sentence description of what the workflow accomplishes. Shown in the blueprint header. |

!!! note "No manual bindings"
    Data flow between steps is **not** declared by hand. The blueprint's
    "Observed Request & Response Payloads" section renders the actual request
    and response body of each step (captured from the passing test run, with
    secret-looking fields redacted), so a consuming agent can match field
    names and example values across steps itself — including cases where a
    value is transformed (e.g. wrapped in `Bearer `) before a later step uses
    it.

### `step_boundary(domain, name)`

A context manager. Use it for non-HTTP steps that an integrator will need to
implement themselves: client-side calculations, mocked external services,
queued work, etc.

- `domain` becomes the "Domain / Boundary" column in the blueprint table.
- `name` becomes the row's action label.

## `AgentTestClient`

A subclass of `starlette.testclient.TestClient`. Construct it exactly the
way you would the standard test client:

```python
from agent_grammar import AgentTestClient
from app.main import app

client = AgentTestClient(app)
```

Every `client.request(...)`, `client.get(...)`, `client.post(...)`, etc.
issued from inside a `@workflow`-decorated test is appended to the active
recorder as an `HttpStep` with method, path, request JSON, status code, and
response JSON (when parseable).

Requests issued outside any active `@workflow` are not recorded.

## Serving helpers

Importable from `agent_grammar.serve.fastapi`.

### `GrammarRouter(filepath, *, reload=False)`

::: agent_grammar.serve.fastapi.GrammarRouter
    options:
      show_root_heading: false

| Argument | Type | Default | Description |
|---|---|---|---|
| `filepath` | `str \| Path` | — | Path to the compiled `workflows.md`. |
| `reload` | `bool` | `False` | If `True`, re-read the file on every request (dev mode). If `False`, the file is read once at construction time and cached in memory. |

Mount it with a versioned prefix to match the URL pattern that
`agent-grammar export-agent-docs` advertises in the platform rule files:

```python
app.include_router(
    GrammarRouter(filepath="assets/workflows.md"),
    prefix="/v1/agent-workflows",
)
```

Raises `FileNotFoundError` at construction if the file doesn't exist, and
`ImportError` if FastAPI isn't installed (install with
`pip install "agent-grammar[fastapi]"`).

### `AgentTelemetryMiddleware`

| Argument | Type | Default | Description |
|---|---|---|---|
| `app` | ASGI app | — | The app to wrap (passed by `add_middleware`). |
| `on_detect` | `Callable[[str], None] \| None` | `None` | Called with the workflow ID when a 2xx response carries the `X-Agent-Grammar-Workflow` header. |

The callback runs after the response is generated. Exceptions raised by the
callback are logged at the `agent_grammar.serve` logger and swallowed —
business traffic is never broken by a telemetry failure.

The header constant is exported as
`agent_grammar.serve.fastapi.TELEMETRY_HEADER` (`"X-Agent-Grammar-Workflow"`).

## CLI: `agent-grammar export-agent-docs`

Generates platform-specific system-prompt files for the major AI coding
assistants.

```bash
agent-grammar export-agent-docs \
    --base-url https://api.example.com \
    --api-version v1
```

| Flag | Type | Default | Description |
|---|---|---|---|
| `--base-url` | URL | **required** | Production base URL of the API (e.g. `https://api.example.com`). |
| `--api-version` | str | `v1` | API version namespace. Used both in the rendered fetch URL and in the default local cache path. |
| `--output-dir` | path | `./agent-docs` | Directory to write the platform rule files into. |
| `--workflows-path` | path | `.agent/workflows_{version}.md` | Local cache path the agent should use for downloaded workflows. |
| `--platform` | choice | all four | One of `cursor`, `claude`, `copilot`, `gemini`. Pass multiple times to select a subset. |

Output:

```
agent-docs/
├── cursor-rules.md
├── claude-rules.md
├── copilot-rules.md
└── gemini-rules.md
```

Each file is a Jinja2 render of the corresponding template under
`src/agent_grammar/templates/`. The rendered URL has the form
`{base_url}/{api_version}/agent-workflows`.

## Logging

The package uses two loggers — both off by default; configure them with your
preferred logging setup:

- `agent_grammar.serve` — emits an exception traceback when an
  `AgentTelemetryMiddleware` callback raises.

Workflow recording itself is silent.
