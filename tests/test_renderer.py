"""Golden-file test for MarkdownRenderer.

Locks the wire format so any regression is caught immediately.
"""

from __future__ import annotations

from pathlib import Path

from agent_grammar._models import (
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


def test_renderer_renders_payloads_for_bodyless_request() -> None:
    record = WorkflowRecord(
        name="Solo",
        slug=slugify("Solo"),
        intent="single-step flow",
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
    assert "### 2. Observed Request & Response Payloads" in rendered
    # A GET with no request body renders an explicit no-body marker.
    assert "_(no body)_" in rendered
    assert '"ok": true' in rendered


def test_renderer_redacts_secret_fields() -> None:
    record = WorkflowRecord(
        name="Auth",
        slug=slugify("Auth"),
        intent="token flow",
        steps=[
            HttpStep(
                method="POST",
                path="/v1/auth/token",
                request_json={"password": "hunter2"},
                status_code=200,
                response_json={"access_token": "super-secret-value"},
            )
        ],
    )
    rendered = MarkdownRenderer().render([record])
    assert "hunter2" not in rendered
    assert "super-secret-value" not in rendered
    assert "[REDACTED]" in rendered


def test_slugify_lowercases_and_underscores() -> None:
    assert slugify("Material Onboarding Lifecycle") == "material_onboarding_lifecycle"
    assert slugify("  Hello, World!  ") == "hello_world"
    assert slugify("v1/Auth-Token") == "v1_auth_token"
