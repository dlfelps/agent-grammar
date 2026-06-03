"""Golden-file test for MarkdownRenderer.

Locks the wire format so any regression is caught immediately.
"""

from __future__ import annotations

from pathlib import Path

from agent_grammar._models import (
    Binding,
    BoundaryStep,
    HttpStep,
    WorkflowRecord,
    slugify,
)
from agent_grammar.testing.renderer import MarkdownRenderer

FIXTURES = Path(__file__).parent / "fixtures"


def _build_material_record() -> WorkflowRecord:
    return WorkflowRecord(
        name="Material Onboarding Lifecycle",
        slug=slugify("Material Onboarding Lifecycle"),
        intent=(
            "Secure an identity token, query the local database for a zone, "
            "and register an asset."
        ),
        bindings=[
            Binding(
                source="Step 1.response.access_token",
                target="Step 3.headers.Authorization",
            ),
            Binding(
                source="Step 2.mocked_db_result",
                target="Step 3.body.assigned_zone",
            ),
        ],
        steps=[
            HttpStep(
                method="POST",
                path="/v1/auth/token",
                request_json={"seed": "dev-token"},
                status_code=200,
                response_json={"access_token": "abc"},
            ),
            BoundaryStep(
                domain="Database",
                name="Query PostgreSQL for Zone UUID",
            ),
            HttpStep(
                method="POST",
                path="/v1/materials",
                request_json={"sku": "MAT-9901", "assigned_zone": "z-1"},
                status_code=201,
                response_json={"id": "mat-001"},
            ),
        ],
    )


def test_renderer_matches_golden_fixture() -> None:
    record = _build_material_record()
    rendered = MarkdownRenderer().render([record])
    expected = (FIXTURES / "expected_workflows.md").read_text(encoding="utf-8")
    assert rendered == expected


def test_renderer_handles_empty_bindings() -> None:
    record = WorkflowRecord(
        name="Solo",
        slug=slugify("Solo"),
        intent="single-step flow",
        bindings=[],
        steps=[
            HttpStep(
                method="GET",
                path="/v1/ping",
                request_json=None,
                status_code=200,
                response_json={"ok": True},
            )
        ],
    )
    rendered = MarkdownRenderer().render([record])
    assert "## Workflow: Solo" in rendered
    assert "_(none)_" in rendered


def test_slugify_lowercases_and_underscores() -> None:
    assert slugify("Material Onboarding Lifecycle") == "material_onboarding_lifecycle"
    assert slugify("  Hello, World!  ") == "hello_world"
    assert slugify("v1/Auth-Token") == "v1_auth_token"
