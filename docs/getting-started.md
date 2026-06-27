# Getting started

This page gives you the mental model and a working first run in about five minutes. For deeper
dives, follow the links to the dedicated guides.

## What it is

The DevOps AI Toolkit reads operational text — container logs, Kubernetes manifests, Terraform
files, command output, raw error strings — and returns **ranked root causes**, **read-only
diagnostic commands**, **suggested fixes**, **references**, and **prevention advice**.

Three things make it different:

1. **Read-only.** It never runs a command or changes infrastructure. Every diagnostic command it
   suggests is non-mutating, and fixes are described as guidance — never auto-applied. See
   [Security](security.md).
2. **Offline-first and deterministic.** A packaged knowledge base of YAML *signatures* powers the
   analysis with **no API key required**. The same input always yields the same result. See the
   [Knowledge base](knowledge-base.md).
3. **One engine, three interfaces.** A single `AnalysisEngine` powers the CLI, the Python SDK, and
   the REST API. There is no duplicated business logic. See [Architecture](architecture.md).

## Install

```bash
pip install devops-ai-toolkit          # core: CLI + SDK, fully offline
pip install 'devops-ai-toolkit[api]'   # add the FastAPI REST server
```

Full options (including `uv` for development) are in [Installation](installation.md).

## Your first analysis

### CLI

```bash
# Analyze a file
devops-ai analyze nova.log

# Explain a known error by name
devops-ai explain CrashLoopBackOff

# Pipe in command output
kubectl get pods | devops-ai analyze -
```

### Python SDK

```python
from devops_ai_toolkit import AnalysisEngine

engine = AnalysisEngine()
result = engine.analyze_file("nova.log")

print(result.summary)
for cause in result.root_causes:
    print(f"[{cause.confidence_percent}%] {cause.title}")
```

### REST API

```bash
devops-ai serve --port 8000
curl -s localhost:8000/analyze/log \
  -H 'content-type: application/json' \
  -d '{"content": "Back-off restarting failed container"}' | jq .summary
```

## Optional: AI enrichment

Everything above works offline. To add an LLM-written narrative on top of the deterministic
findings, configure a provider and pass `--enrich` (CLI) or `enrich=True` (SDK/API):

```bash
export DEVOPS_AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
devops-ai analyze nova.log --enrich
```

See [AI providers](ai-providers.md) and [Configuration](configuration.md).

## Where to go next

- [Quickstart](quickstart.md) — a guided first run across all three interfaces
- [CLI guide](cli-guide.md) / [SDK guide](sdk-guide.md) / [REST API guide](rest-api-guide.md)
- [Output format](output-format.md) — understand every field you get back
- [Use cases](use-cases.md) — apply it to real incidents

Need a hosted assistant instead of self-hosting? Try the
[AI incident-response assistant](https://devopsaitoolkit.com/dashboard/incident-response).
