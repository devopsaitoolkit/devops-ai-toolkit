# Comparison

How the DevOps AI Toolkit differs from the tools you might reach for instead. Short version: it's
**deterministic, offline-first, and read-only**, and it speaks one contract across CLI, SDK, and
API.

## vs. raw LLM chat (ChatGPT / Claude / Gemini)

| Aspect            | Raw LLM chat                          | DevOps AI Toolkit                                  |
|-------------------|---------------------------------------|---------------------------------------------------|
| Determinism       | Non-deterministic; answers vary       | Deterministic core; same input → same output      |
| Offline           | Requires the vendor API               | Works fully offline, **no API key required**       |
| Provenance        | Often unsourced                       | Findings come from auditable YAML signatures with references |
| Cost              | Per-token for every query             | Free for deterministic analysis; LLM only on opt-in `--enrich` |
| Read-only safety  | May suggest destructive commands      | **Read-only by design**; only non-mutating commands |
| Integration       | Copy-paste into a chat box            | CLI, SDK, and REST API on one engine              |
| Data exposure     | Sends your logs to a vendor           | Sends nothing by default; enrichment is opt-in (and can be local Ollama) |

The toolkit can *also* call an LLM — but as **optional enrichment layered on top of** the
deterministic result, not as the source of truth. See [AI providers](ai-providers.md).

## vs. kubectl plugins (krew tools, `kubectl debug`, etc.)

| Aspect            | kubectl plugins                       | DevOps AI Toolkit                                  |
|-------------------|---------------------------------------|---------------------------------------------------|
| Scope             | Kubernetes-only                       | Kubernetes **and** Terraform, Docker, OpenStack, Linux, databases, and more |
| Action model      | Often act on the cluster              | Never acts; analyzes text and suggests commands    |
| Input             | Live cluster access required          | Any text: logs, manifests, command output, error strings |
| Where it runs     | Needs cluster credentials             | Runs anywhere, on captured text — great for air-gapped/post-mortem |
| Output            | Tool-specific                         | One structured `AnalysisResult` across interfaces  |

Use kubectl plugins to *gather* state; use the toolkit to *interpret* the text they produce —
offline and safely. See [Supported technologies](supported-technologies.md).

## vs. log-analysis / observability platforms

Observability platforms excel at collection, dashboards, and alerting. The toolkit is
complementary: feed an alert payload or a log excerpt to the engine to get a ranked root cause and
the read-only commands to confirm it. It's lightweight, embeddable (SDK), and needs no agents.

## vs. internal runbooks / wikis

Runbooks go stale and aren't queryable. Encoding the same knowledge as
[signatures](knowledge-base.md) makes it deterministic, testable, versioned, and instantly
queryable from CLI, SDK, or API — turning tribal knowledge into a living catalog.

## When to reach for something else

- You need to **take action** automatically — the toolkit is intentionally read-only.
- You need **collection/alerting** infrastructure — use an observability platform and feed its
  output here.
- You want a **fully managed** assistant with escalation — try the
  [AI incident assistant](https://devopsaitoolkit.com/dashboard/incident-response).

## See also

- [Architecture](architecture.md) — why one engine matters
- [Use cases](use-cases.md) — where it fits in real workflows
