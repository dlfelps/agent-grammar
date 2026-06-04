# agent-grammar vs. fastapi-mcp

Both projects connect AI agents to a FastAPI service, so they are easy to
confuse. They solve opposite halves of the problem, and the difference comes
down to a single question:

> **Do you want the agent to *call* your API, or to *write code that calls*
> your API?**

[`fastapi-mcp`](https://github.com/tadata-org/fastapi_mcp) makes the agent
**self-sufficient** — it exposes your endpoints as [Model Context
Protocol](https://modelcontextprotocol.io/) tools so the agent can invoke them
directly at runtime. `agent-grammar` makes the agent a **better coder** — it
publishes a test-gated workflow contract that the agent reads while it writes
integration code for a developer to ship.

## Side by side

| | `agent-grammar` | `fastapi-mcp` |
|---|---|---|
| **Goal** | Make the agent a better *coder* | Make the agent *self-sufficient* |
| **When the agent acts** | Authoring time — generating integration code | Runtime — fulfilling a user request |
| **What the agent receives** | A `workflows.md` blueprint (ordered steps + observed payloads) to read | Live MCP tools it can invoke |
| **Who runs the API call** | The developer's shipped code, later | The agent, immediately |
| **Source of truth** | Your passing `pytest` integration tests | Your live endpoint signatures |
| **Multi-step data flow** | Captured from real test runs and shown explicitly | The agent must discover it by trial and error |
| **Primary output** | Documentation / per-platform rule files | A running MCP server |
| **Best when** | Third-party developers integrate against your API | You want an agent to operate the API for an end user |

## What "make the agent a better coder" means

`agent-grammar` never puts the agent in the request path. Instead it gives the
agent the one thing a longer prompt can't: a contract derived from tests that
actually passed. The agent reads the ordered execution sequence and the
**observed** request/response payloads, then emits integration code whose
endpoints, parameter names, and call ordering match reality — no hallucinated
routes, no guessed field names, no missing dependency between two calls.

That code is reviewed and shipped by a human. The agent's job is to *write it
correctly the first time*, not to run it.

## What "make the agent self-sufficient" means

`fastapi-mcp` mounts your endpoints as MCP tools so an agent can execute them
on its own to satisfy a user's request — booking a ticket, querying a record,
triggering a job. The agent is the one making the live calls, which is exactly
what you want for an autonomous assistant, but it also means the agent
discovers your API's quirks at runtime and any mistake is a real API call
against a real system.

## They are complementary

These approaches are not mutually exclusive. A common pairing:

- Use **`fastapi-mcp`** to let an internal agent *operate* the API directly.
- Use **`agent-grammar`** to let external developers' agents *generate correct
  integration code* against the same API, gated by your test suite.

If your priority is helping people (and their coding assistants) build
**correct integrations** against your API, reach for `agent-grammar`. If your
priority is letting an agent **drive** the API itself, reach for `fastapi-mcp`.
