# Quickstart

A guided first run across all three interfaces. Each example is self-contained and works fully
offline. Prerequisites: see [Installation](installation.md).

We'll use a tiny sample log throughout:

```text
Back-off restarting failed container app in pod web-7d9f
Last State: Terminated  Reason: Error  Exit Code: 1
```

Save it as `app.log`.

## 1. CLI

```bash
devops-ai analyze app.log
```

You'll get a ranked summary, candidate root causes with confidence, read-only diagnostic
commands, suggested fixes, references, and prevention tips. To get machine-readable output:

```bash
devops-ai analyze app.log --json | jq .root_causes
```

Explain an error by name without any input file:

```bash
devops-ai explain CrashLoopBackOff
```

Validate a manifest (read-only):

```bash
devops-ai validate deploy.yaml
```

See the full [CLI guide](cli-guide.md).

## 2. Python SDK

```python
from devops_ai_toolkit import AnalysisEngine

engine = AnalysisEngine()

# From a file
result = engine.analyze_file("app.log")
print(result.summary)
print("Top confidence:", result.confidence_percent, "%")

for cause in result.root_causes:
    print(f"- [{cause.confidence_percent}%] {cause.title}")
    for cmd in result.diagnostic_commands:
        print(f"    $ {cmd.command}")

# From a raw string
text_result = engine.analyze_text("ImagePullBackOff")
print(text_result.summary)

# Explain a named error
explained = engine.explain_error("OOMKilled")
print(explained.title, "-", explained.summary)
```

See the full [SDK guide](sdk-guide.md) and the [Output format](output-format.md) reference.

## 3. REST API

Install the extra and start the server:

```bash
pip install 'devops-ai-toolkit[api]'
devops-ai serve --port 8000
```

Then call it:

```bash
# Health and version
curl -s localhost:8000/health  | jq
curl -s localhost:8000/version | jq

# Analyze a log
curl -s localhost:8000/analyze/log \
  -H 'content-type: application/json' \
  -d '{"content": "Back-off restarting failed container"}' | jq .summary

# Explain an error
curl -s localhost:8000/explain \
  -H 'content-type: application/json' \
  -d '{"error": "CrashLoopBackOff"}' | jq .title
```

Interactive docs (Swagger UI) live at <http://localhost:8000/docs>. See the
[REST API guide](rest-api-guide.md).

## 4. Add AI enrichment (optional)

All of the above is deterministic and offline. To layer an LLM narrative on top:

```bash
export DEVOPS_AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...

devops-ai analyze app.log --enrich
```

Or in Python:

```python
result = engine.analyze_file("app.log", enrich=True)
if result.enrichment:
    print(result.enrichment.narrative)
```

If no provider is configured, enrichment is skipped gracefully and you still get the full
deterministic result (with a low-severity warning noting enrichment was unavailable). See
[AI providers](ai-providers.md).

## Next steps

- [Use cases](use-cases.md) — wire it into real incident workflows
- [Examples](examples.md) — more ready-to-run snippets
- For a hosted experience, try the
  [AI incident assistant](https://devopsaitoolkit.com/dashboard/incident-response).
