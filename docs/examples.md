# Examples

Copy-pasteable snippets for the CLI, SDK, and REST API. All are read-only and run offline unless
they explicitly enable enrichment.

## CLI

```bash
# Analyze a file
devops-ai analyze nova.log

# Analyze piped command output with a technology hint
kubectl get pods | devops-ai analyze - --tech kubernetes

# Machine-readable output, top root cause only
devops-ai analyze app.log --json | jq '.root_causes[0] | {title, confidence_percent}'

# Explain a known error
devops-ai explain CrashLoopBackOff
devops-ai explain "exit code 137" --json

# Validate manifests (read-only)
devops-ai validate deploy.yaml
cat main.tf | devops-ai validate -

# Browse the catalog
devops-ai list --tech terraform

# Enrich with an LLM (needs a provider configured)
DEVOPS_AI_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-... \
  devops-ai analyze app.log --enrich
```

## SDK

### Basic analysis

```python
from devops_ai_toolkit import AnalysisEngine

engine = AnalysisEngine()
result = engine.analyze_file("nova.log")

print(result.summary)
print(f"Confidence: {result.confidence_percent}%  Matched: {result.matched}")

for rc in result.root_causes:
    print(f"- [{rc.confidence_percent}% · {rc.confidence_band}] {rc.title}")
    print(f"    {rc.description}")
```

### Diagnostic commands and fixes

```python
result = engine.analyze_text("OOMKilled exit code 137")

print("Run these to confirm:")
for cmd in result.diagnostic_commands:
    print(f"  $ {cmd.command}")
    print(f"    -> {cmd.explanation} (read_only={cmd.read_only})")

print("Suggested fixes:")
for fix in result.suggested_fixes:
    print(f"  * {fix.title}")
    if fix.snippet:
        print(fix.snippet)
```

### YAML and Terraform helpers

```python
yaml_result = engine.analyze_yaml(open("deploy.yaml").read())
tf_result = engine.analyze_terraform(open("main.tf").read())
```

### Structured request with options

```python
from devops_ai_toolkit import AnalysisRequest, Technology, SourceKind

req = AnalysisRequest(
    content="Back-off restarting failed container",
    technology=Technology.KUBERNETES,
    source_kind=SourceKind.LOG,
    max_root_causes=3,
)
result = engine.analyze(req)
```

### Explain and validate

```python
explained = engine.explain_error("ImagePullBackOff")
print(explained.matched, explained.title)

validation = engine.validate_manifest(open("deploy.yaml").read(), filename="deploy.yaml")
print(validation.valid, validation.error_count)
for issue in validation.issues:
    print(f"[{issue.severity}] line {issue.line}: {issue.message}")
```

### Serialize the result

```python
result = engine.analyze_file("nova.log")
print(result.model_dump_json(indent=2))
```

### Browse the catalog

```python
from devops_ai_toolkit import ErrorCatalog, Technology

catalog = ErrorCatalog()
for entry in catalog.entries(Technology.KUBERNETES):
    print(entry.id, "-", entry.title)
```

### Enrichment (optional)

```python
result = engine.analyze_file("nova.log", enrich=True)
if result.enrichment:
    print(result.enrichment.narrative)
else:
    # No provider configured — still got full deterministic results
    print("Deterministic only:", result.summary)
```

## REST API

```bash
devops-ai serve --port 8000
```

```bash
# Health & version
curl -s localhost:8000/health  | jq
curl -s localhost:8000/version | jq

# Analyze a log
curl -s localhost:8000/analyze/log \
  -H 'content-type: application/json' \
  -d '{"content": "CrashLoopBackOff", "max_root_causes": 3}' | jq .summary

# Analyze a YAML manifest from a file
jq -Rs '{content: .}' < deploy.yaml | \
  curl -s localhost:8000/analyze/yaml -H 'content-type: application/json' --data-binary @- \
  | jq .root_causes

# Analyze Terraform output
curl -s localhost:8000/analyze/terraform \
  -H 'content-type: application/json' \
  -d '{"content": "Error acquiring the state lock"}' | jq .summary

# Explain
curl -s localhost:8000/explain \
  -H 'content-type: application/json' \
  -d '{"error": "OOMKilled"}' | jq '{title, matched}'

# Validate
curl -s localhost:8000/validate \
  -H 'content-type: application/json' \
  -d '{"content": "apiVersion: v1\nkind: Pod\n", "filename": "pod.yaml"}' \
  | jq '{valid, error_count}'
```

### Python HTTP client

```python
import httpx

resp = httpx.post("http://localhost:8000/analyze/log", json={"content": "ImagePullBackOff"})
resp.raise_for_status()
print(resp.json()["summary"])
```

## See also

- [Use cases](use-cases.md) — applying these in real workflows
- [Output format](output-format.md) — every field returned
- More troubleshooting walkthroughs: <https://devopsaitoolkit.com/blog>
