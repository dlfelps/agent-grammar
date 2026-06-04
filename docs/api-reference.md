# API Reference

Auto-generated from docstrings in the `agent_grammar` package.

## Top-level exports

These three symbols are re-exported from `agent_grammar` and form the surface
you'll touch when annotating a test:

### `workflow`

::: agent_grammar.workflow

### `step_boundary`

::: agent_grammar.step_boundary

### `AgentTestClient`

::: agent_grammar.AgentTestClient

## Data models

::: agent_grammar._models.HttpStep

::: agent_grammar._models.BoundaryStep

::: agent_grammar._models.WorkflowRecord

## Serving (`agent_grammar.serve.fastapi`)

### `GrammarRouter`

::: agent_grammar.serve.fastapi.GrammarRouter

### `AgentTelemetryMiddleware`

::: agent_grammar.serve.fastapi.AgentTelemetryMiddleware

## CLI (`agent_grammar.cli`)

The CLI is a [Click](https://click.palletsprojects.com/) command group with a
single subcommand, `export-agent-docs`. See
[Configuration → CLI](configuration.md#cli-agent-grammar-export-agent-docs)
for flag-by-flag documentation.

::: agent_grammar.cli.export.export_agent_docs
