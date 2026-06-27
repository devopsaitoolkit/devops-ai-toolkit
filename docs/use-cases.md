# Use cases

Practical ways teams put the toolkit to work. Every workflow below is **read-only** — nothing here
runs a remediation or mutates infrastructure.

## 1. Fast incident triage from the terminal

Pipe the most relevant output straight into the analyzer to get a ranked hypothesis and read-only
commands to confirm it:

```bash
kubectl logs my-pod --previous | devops-ai analyze - --tech kubernetes
```

The result tells you the most likely cause, the diagnostic commands to verify it, and a suggested
fix — without you having to remember the right `kubectl` incantation.

## 2. On-call runbook lookups

Instead of digging through wikis, ask the catalog directly:

```bash
devops-ai explain CrashLoopBackOff
devops-ai explain "exit code 137"
devops-ai explain "Error acquiring the state lock"
```

Pair it with the hosted
[AI incident assistant](https://devopsaitoolkit.com/dashboard/incident-response) for live
escalations.

## 3. CI gate on known failure patterns

Use the exit codes to fail fast when a build trips a catalogued error:

```bash
terraform plan 2>&1 | devops-ai analyze - --tech terraform
if [ $? -eq 0 ]; then
  echo "::warning::Known Terraform failure pattern detected"
fi
```

`analyze` exits `0` on a match, `1` on no match, `2` on input errors. See the [CLI guide](cli-guide.md).

## 4. Pre-deploy manifest validation

Catch problems before they reach the cluster, read-only:

```bash
devops-ai validate deploy.yaml
devops-ai validate main.tf
```

Wire it into a pre-commit hook or CI step.

## 5. Programmatic enrichment in your own tooling

Embed the engine in dashboards, bots, or internal tools via the SDK:

```python
from devops_ai_toolkit import AnalysisEngine

engine = AnalysisEngine()

def triage(log_text: str) -> dict:
    result = engine.analyze_text(log_text, enrich=True)
    return {
        "summary": result.summary,
        "confidence": result.confidence_percent,
        "top_fix": result.suggested_fixes[0].title if result.suggested_fixes else None,
    }
```

## 6. A shared HTTP service for your platform team

Run the REST API once and let every team query it:

```bash
devops-ai serve --host 0.0.0.0 --port 8000
```

```bash
curl -s platform-svc:8000/analyze/log \
  -H 'content-type: application/json' \
  -d '{"content": "ImagePullBackOff"}' | jq .summary
```

Same engine, same results as the CLI and SDK. See the [REST API guide](rest-api-guide.md).

## 7. ChatOps integration

Forward a Slack message or alert payload to the engine and post back the summary plus the top
diagnostic command. Because output is structured JSON, it's trivial to format for chat.

## 8. Private / air-gapped analysis

The deterministic engine needs no network. For environments that still want an LLM narrative
without sending data to a vendor, point it at a local [Ollama](ai-providers.md) instance:

```bash
export DEVOPS_AI_PROVIDER=ollama
devops-ai analyze incident.log --enrich
```

## 9. Building your own knowledge base

Capture your organization's recurring incidents as signatures and inject a custom knowledge base —
turning tribal knowledge into a deterministic, queryable catalog. See the
[Plugin guide](plugin-guide.md).

## See also

- [Examples](examples.md) — copy-pasteable snippets
- [Output format](output-format.md) — wire results into your own UI
- Subscribe for new patterns and guides: <https://devopsaitoolkit.com/newsletter>
