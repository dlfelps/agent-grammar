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

### 2. Precise Parameter Bindings & Payloads
| Target Input Field | Source Reference Property | Logic for Generated Code |
|---|---|---|
| `POST /v1/materials.headers.Authorization` | `Step 1.response.access_token` | Extract token from Step 1 response and prefix with 'Bearer '. |
| `POST /v1/materials.body.assigned_zone` | `Step 2 Database Query Result` | Store the external DB zone ID in a variable and map it to the JSON payload. |
