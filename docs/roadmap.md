# Roadmap

The toolkit's strategy is simple: **build every surface on the one shared engine.** New interfaces
are thin adapters, so they inherit the same read-only, offline-first, deterministic behaviour for
free. See [Architecture](architecture.md).

## Available now

- **CLI** (`devops-ai`) — analyze, explain, validate, list, serve, version. See
  [CLI guide](cli-guide.md).
- **Python SDK** — `AnalysisEngine` and the public models. See [SDK guide](sdk-guide.md).
- **REST API** — FastAPI with Swagger/ReDoc. See [REST API guide](rest-api-guide.md).
- **Extensibility** — YAML signatures and pluggable AI providers via `register_provider()`. See
  [Plugin guide](plugin-guide.md).
- **Providers** — Anthropic, OpenAI, Gemini, Ollama, plus the offline default.

## Planned

These are design directions, not commitments. Each reuses the engine — none reimplements analysis.

| Surface              | Idea                                                                 | Design note |
|----------------------|----------------------------------------------------------------------|-------------|
| **Web UI**           | Browser front-end over the REST API for paste-and-analyze + browsing | [web-ui.md](web-ui.md) |
| **VS Code extension**| Analyze the active file / selection / terminal output inline         | [vscode-extension.md](vscode-extension.md) |
| **GitHub Action**    | Analyze CI logs and manifests in pipelines; annotate PRs             | [github-action.md](github-action.md) |
| **MCP server**       | Expose analyze/explain/validate as tools to AI agents                | [mcp-server.md](mcp-server.md) |
| **Desktop app**      | Offline, local desktop wrapper for operators                         | — |

## Ongoing

- **Broader knowledge base** — more signatures across the [supported technologies](supported-technologies.md)
  and new ones. Contributions welcome; it's just YAML. See [Knowledge base](knowledge-base.md).
- **Smarter detection and ranking** — improved technology/source-kind detection and scoring.
- **More providers** — additional adapters as the ecosystem evolves.

## Principles that won't change

- **Read-only.** No surface will ever execute commands or mutate infrastructure. See
  [Security](security.md).
- **Offline-first & deterministic.** The core never requires an API key; LLMs stay optional.
- **One engine.** Every interface is a thin adapter over `AnalysisEngine`.
- **Additive contracts.** `AnalysisResult` grows by addition so interfaces never drift.

## Get involved

- Propose or build a surface — open an issue or PR. See [Contributing](contributing.md).
- Follow progress: <https://devopsaitoolkit.com/blog> and <https://devopsaitoolkit.com/newsletter>.
