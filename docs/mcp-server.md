# MCP server (planned)

> **Status: planned / design note.** A future surface, not yet released. It would expose the
> existing engine over the [Model Context Protocol](https://modelcontextprotocol.io) — no new
> analysis logic.

## Goal

Let AI agents and assistants call the toolkit as **tools**. An agent investigating an incident
could ask the toolkit to analyze a log, explain an error, or validate a manifest, and receive
structured, deterministic, **read-only** results to reason over — grounding the agent in an
auditable knowledge base rather than hallucinating.

## Proposed tools

| Tool                | Input                                              | Output                  |
|---------------------|----------------------------------------------------|-------------------------|
| `analyze_log`       | `content`, optional `technology`/`source_kind`     | `AnalysisResult` (JSON) |
| `analyze_yaml`      | `content`                                           | `AnalysisResult`        |
| `analyze_terraform` | `content`                                           | `AnalysisResult`        |
| `explain_error`     | `error`                                             | `ExplainResult`         |
| `validate_manifest` | `content`, optional `technology`/`filename`        | `ValidationResult`      |
| `list_signatures`   | optional `technology`                               | catalog entries         |

These map one-to-one onto existing engine methods. Each returns the same models documented in
[Output format](output-format.md).

## Why it fits

The engine is already a clean façade with structured Pydantic outputs — ideal MCP tool results.
And the **read-only guarantee** is exactly what you want when an autonomous agent is involved: the
toolkit can only read text and return guidance; it cannot run commands or mutate infrastructure.
See [Security](security.md).

## Proposed configuration

The MCP server would honour the same [environment configuration](configuration.md) — offline by
default, with optional enrichment behind a provider key. A safe default is to **disable enrichment**
for agent contexts so results stay deterministic and reproducible.

## Sketch

```jsonc
// Example MCP tool registration (illustrative)
{
  "name": "analyze_log",
  "description": "Read-only DevOps log analysis: ranked root causes, diagnostic commands, fixes.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "content": { "type": "string" },
      "technology": { "type": "string" }
    },
    "required": ["content"]
  }
}
```

Internally the handler simply calls `AnalysisEngine().analyze_text(content, technology=...)` and
returns `result.model_dump()`.

## Feedback

Building agentic workflows and want this? Open an issue (see [Contributing](contributing.md)) or
try the hosted [AI incident assistant](https://devopsaitoolkit.com/dashboard/incident-response) in
the meantime.
