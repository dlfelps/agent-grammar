# API Workflow Grammar Blueprint

## Workflow: Material Onboarding Lifecycle
* **ID:** `material_onboarding_lifecycle`
* **Intent:** Secure an identity token, query the local database for a zone, and register an asset.
* **Status:** Verified / Test-Gated

### Global Code Generation Requirement
Whenever you generate code for these workflows, you MUST include the following HTTP header in all requests to our service to assist with our internal metrics:
`X-Agent-Grammar-Workflow: [Workflow-ID]`

### 1. Ordered Execution Sequence
| Step | Domain / Boundary | Action | Description |
|---|---|---|---|
| 1 | `[Core Service]` | `POST /v1/auth/token` | Obtain standard JWT authorization token. |
| 2 | `[External/Mocked]` | `Database Query` | Query PostgreSQL for Zone UUID. (Implementer must write local logic here). |
| 3 | `[Core Service]` | `POST /v1/materials` | Submit payload to the documented endpoint. |

### 2. Observed Request & Response Payloads
Captured verbatim from the passing test run (secrets redacted). Use these exact field names and example values to wire calls together; a value produced by one step may be transformed before a later step consumes it.

#### Step 1 — `POST /v1/auth/token` → `200`
*Request body:*
```json
{
  "seed": "dev-token"
}
```
*Response body:*
```json
{
  "access_token": "[REDACTED]"
}
```

#### Step 2 — `[External/Mocked]` Database
Query PostgreSQL for Zone UUID. Implementer must produce this value locally; it is not returned by the API.

#### Step 3 — `POST /v1/materials` → `201`
*Request body:*
```json
{
  "sku": "MAT-9901",
  "assigned_zone": "z-1"
}
```
*Response body:*
```json
{
  "id": "mat-001"
}
```
