# DevOps AI Toolkit — Documentation

AI-powered, **read-only** DevOps troubleshooting for logs, YAML, Terraform, Kubernetes,
OpenStack and more. One shared analysis engine powers a CLI, a Python SDK, and a REST API —
so you get identical behaviour everywhere.

> The toolkit is **read-only**: it inspects text and produces guidance. It never executes
> commands, mutates files, or touches your infrastructure. It is **offline-first**: a packaged
> knowledge base of YAML "signatures" does the analysis with **no API key required**. Optional
> LLM providers add narrative enrichment behind a vendor-agnostic adapter.

```python
from devops_ai_toolkit import AnalysisEngine

result = AnalysisEngine().analyze_file("nova.log")
print(result.summary)
```

```bash
pip install devops-ai-toolkit
devops-ai analyze nova.log
devops-ai explain CrashLoopBackOff
```

## Table of contents

### Get started
- [Getting started](getting-started.md) — the 5-minute overview
- [Installation](installation.md) — core, API extra, and `uv`-based dev installs
- [Quickstart](quickstart.md) — first analysis in CLI, SDK, and REST

### Using the toolkit
- [CLI guide](cli-guide.md) — every `devops-ai` command
- [SDK guide](sdk-guide.md) — `AnalysisEngine` from Python
- [REST API guide](rest-api-guide.md) — HTTP endpoints and Swagger
- [Configuration](configuration.md) — environment variables and tunables
- [AI providers](ai-providers.md) — the adapter model (Anthropic/OpenAI/Gemini/Ollama)
- [Output format](output-format.md) — the result sections explained
- [Supported technologies](supported-technologies.md) — what the knowledge base covers
- [Use cases](use-cases.md) — real workflows
- [Examples](examples.md) — copy-pasteable snippets

### Plugins
- [Plugins](plugins.md) — the plugin architecture: the `AnalyzerPlugin` interface, discovery, lifecycle, and CLI/REST
- [Plugin development](plugin-development.md) — scaffold, test, package, and publish a plugin
- [Plugin marketplace](plugin-marketplace.md) — the `PluginMetadata` schema and the registry vision
- [Enterprise plugins](enterprise-plugins.md) — private, signed, offline, and pinned plugins; the trust model
- [LLM providers](llm-providers.md) — the provider plugin point (Anthropic/OpenAI/Gemini/Azure/Ollama/null)

### Understanding it
- [Architecture](architecture.md) — clean architecture and the shared engine
- [Knowledge base](knowledge-base.md) — how signatures work and how to add one
- [Security](security.md) — read-only guarantees and key handling
- [Comparison](comparison.md) — vs. raw LLM chat and kubectl plugins
- [Glossary](glossary.md) — terms used throughout
- [Troubleshooting guide](troubleshooting-guide.md) — fixing the toolkit itself
- [FAQ](faq.md)

### Contributing & development
- [Contributing](contributing.md)
- [Developer guide](developer-guide.md)
- [Coding standards](coding-standards.md)
- [Testing guide](testing-guide.md)
- [Plugin guide](plugin-guide.md) — custom providers and signatures
- [Release process](release-process.md)
- [Roadmap](roadmap.md)

### Planned interfaces (design notes)
- [GitHub Action](github-action.md)
- [VS Code extension](vscode-extension.md)
- [MCP server](mcp-server.md)
- [Web UI](web-ui.md)

## Project links

- Website & tutorials: <https://devopsaitoolkit.com>
- Troubleshooting blog: <https://devopsaitoolkit.com/blog>
- AI incident assistant: <https://devopsaitoolkit.com/dashboard/incident-response>
- Newsletter: <https://devopsaitoolkit.com/newsletter>

## License

MIT. See the repository for full text.
