# Installation

## Requirements

- **Python:** 3.10, 3.11, or 3.12
- **pytest:** 7.0 or newer (already a runtime dependency)

## Install from PyPI

=== "Core"

    ```bash
    pip install agent-grammar
    ```

    Installs the pytest plugin, `AgentTestClient`, the markdown renderer, the
    `agent-grammar` CLI, and a Starlette-based `GrammarRouter` for serving the
    compiled workflows.

=== "With FastAPI"

    ```bash
    pip install "agent-grammar[fastapi]"
    ```

    Adds FastAPI as a hard dependency. Use this if your service is FastAPI-
    based and you want to mount `GrammarRouter` directly into your app.

=== "Development"

    ```bash
    pip install -e ".[dev]"
    ```

    Editable install with `pytest-cov`, `mypy`, and `ruff` for local
    development of `agent-grammar` itself.

## Verify the install

Check that the CLI is on your `PATH`:

```bash
agent-grammar --help
```

Confirm the pytest plugin auto-loaded:

```bash
pytest --help | grep agent-grammar
```

You should see the `--agent-grammar-output` and `--agent-grammar-disable`
options listed. The plugin is registered through the
`pytest11` entry point and is discovered automatically once `agent-grammar`
is installed — no `conftest.py` change required.

Smoke-test the import:

```bash
python -c "from agent_grammar import AgentTestClient, step_boundary, workflow; print('ok')"
```

## What gets installed

| Component | Provided by | Used for |
|---|---|---|
| `agent_grammar.workflow` | Python API | Decorate pytest tests to mark them as workflows. |
| `agent_grammar.step_boundary` | Python API | Annotate non-HTTP steps inside a workflow. |
| `agent_grammar.AgentTestClient` | Python API | Drop-in replacement for Starlette's `TestClient` that captures HTTP traffic. |
| `agent_grammar.serve.fastapi.GrammarRouter` | Python API | Mount the compiled `workflows.md` on a versioned route. |
| `agent_grammar.serve.fastapi.AgentTelemetryMiddleware` | Python API | Detect agent-driven requests via the `X-Agent-Grammar-Workflow` header. |
| `agent-grammar` CLI | Console script | Export Claude/Cursor/Copilot/Gemini system-prompt files. |
| pytest plugin | Entry point | Adds `--agent-grammar-output` / `--agent-grammar-disable` and writes the markdown after the session. |

## Next step

Head to the [Walkthrough](walkthrough.md) to clone the demo project, generate
a `workflows.md`, and see the end-to-end loop.
