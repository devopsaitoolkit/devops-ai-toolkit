# REST API guide

The REST API exposes the shared [`AnalysisEngine`](architecture.md) over HTTP. Every route
delegates to a single cached engine instance, so the API has **zero business logic of its own** —
it only marshals JSON. The response models are the same ones the SDK returns, so the two contracts
never drift.

## Install and run

```bash
pip install 'devops-ai-toolkit[api]'

devops-ai serve --host 0.0.0.0 --port 8000
# or
uvicorn devops_ai_toolkit.api.app:app --host 0.0.0.0 --port 8000
```

Interactive documentation is generated automatically:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>

## Endpoints

| Method | Path                  | Purpose                                       |
|--------|-----------------------|-----------------------------------------------|
| GET    | `/health`             | Liveness/readiness + KB & provider status     |
| GET    | `/version`            | Running version                               |
| POST   | `/analyze/log`        | Analyze a log or command output               |
| POST   | `/analyze/yaml`       | Analyze a YAML / Kubernetes manifest          |
| POST   | `/analyze/terraform`  | Analyze Terraform config or plan/apply output |
| POST   | `/explain`            | Explain a known error                         |
| POST   | `/validate`           | Validate a YAML / Kubernetes / Terraform doc  |

## Meta endpoints

### `GET /health`

```bash
curl -s localhost:8000/health | jq
```

```json
{
  "status": "ok",
  "signatures": 42,
  "provider": "null",
  "provider_available": false
}
```

`provider` and `provider_available` reflect your [configuration](configuration.md). Offline by
default (`null` / `false`).

### `GET /version`

```bash
curl -s localhost:8000/version | jq
```

```json
{ "name": "devops-ai-toolkit", "version": "0.1.0" }
```

## Analyze endpoints

All three analyze endpoints accept the same body shape:

```jsonc
{
  "content": "Back-off restarting failed container",  // required, non-empty
  "technology": "kubernetes",        // optional hint, auto-detected if omitted
  "source_kind": "log",              // optional hint, auto-detected if omitted
  "filename": "app.log",             // optional, aids detection
  "enrich": false,                   // add LLM narrative if a provider is configured
  "max_root_causes": 5               // 1-20
}
```

They return an `AnalysisResult` ([Output format](output-format.md#analysisresult)).

```bash
# Log
curl -s localhost:8000/analyze/log \
  -H 'content-type: application/json' \
  -d '{"content": "OOMKilled exit code 137"}' | jq .summary

# YAML / Kubernetes manifest
curl -s localhost:8000/analyze/yaml \
  -H 'content-type: application/json' \
  --data-binary @<(jq -Rs '{content: .}' < deploy.yaml) | jq .root_causes

# Terraform (technology + source kind are inferred as terraform)
curl -s localhost:8000/analyze/terraform \
  -H 'content-type: application/json' \
  -d '{"content": "Error: Error acquiring the state lock"}' | jq .summary
```

## `POST /explain`

```bash
curl -s localhost:8000/explain \
  -H 'content-type: application/json' \
  -d '{"error": "CrashLoopBackOff"}' | jq '{title, matched}'
```

Body: `{ "error": "<name or message>" }`. Returns an `ExplainResult`
([Output format](output-format.md#explainresult)).

## `POST /validate`

```bash
curl -s localhost:8000/validate \
  -H 'content-type: application/json' \
  -d '{"content": "apiVersion: v1\nkind: Pod\n", "filename": "pod.yaml"}' \
  | jq '{valid, error_count, issues}'
```

Body:

```jsonc
{
  "content": "...",         // required
  "technology": null,       // optional
  "source_kind": null,      // optional
  "filename": "pod.yaml"    // optional
}
```

Returns a `ValidationResult` ([Output format](output-format.md#validationresult)).

## Python client example

The response models are pure Pydantic, so any HTTP client works:

```python
import httpx

r = httpx.post(
    "http://localhost:8000/analyze/log",
    json={"content": "ImagePullBackOff"},
)
r.raise_for_status()
data = r.json()
print(data["summary"])
```

## Enabling AI enrichment

Start the server with provider env vars set, then pass `"enrich": true`:

```bash
DEVOPS_AI_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... devops-ai serve

curl -s localhost:8000/analyze/log \
  -H 'content-type: application/json' \
  -d '{"content": "CrashLoopBackOff", "enrich": true}' | jq .enrichment
```

See [AI providers](ai-providers.md) and [Configuration](configuration.md).

## Deployment notes

- The engine is **read-only** — the API performs no mutations and needs no write access. See
  [Security](security.md).
- The engine instance is process-wide and cached (`lru_cache`); the knowledge base loads once.
- Put it behind your own auth/proxy if exposing it beyond localhost; the toolkit ships no auth.
- For a fully hosted alternative, see the
  [AI incident assistant](https://devopsaitoolkit.com/dashboard/incident-response).
