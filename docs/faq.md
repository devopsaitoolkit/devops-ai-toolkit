# FAQ

### Does it need an API key?
No. The deterministic engine works fully offline with the packaged knowledge base. API keys are
only for **optional** LLM enrichment. See [AI providers](ai-providers.md).

### Will it run commands or change my infrastructure?
Never. The toolkit is **read-only**: it reads text and produces guidance. Diagnostic commands are
suggestions you choose to run; fixes are described, never auto-applied. See [Security](security.md).

### Is it deterministic?
Yes — the core engine produces the same output for the same input. Optional LLM enrichment is the
only non-deterministic part, and it's off by default. See [Comparison](comparison.md).

### What can it analyze?
Logs, YAML/Kubernetes manifests, Terraform, Docker, OpenStack, Linux/systemd, databases, message
queues, and more — plus raw command output and error strings. See
[Supported technologies](supported-technologies.md).

### How is this different from asking ChatGPT/Claude?
It's deterministic, offline-first, read-only, and its findings are sourced from auditable
signatures. It can *also* use an LLM — but only as opt-in enrichment on top of the deterministic
result. See [Comparison](comparison.md).

### CLI, SDK, or API — which should I use?
They all run the **same engine**. Use the CLI for ad-hoc triage, the SDK to embed analysis in your
tools, and the REST API to share it as a service. See [Architecture](architecture.md).

### Which Python version?
Python **3.12+**. See [Installation](installation.md).

### How do I add support for an error it doesn't know?
Add a YAML **signature** — no engine code required. See
[Knowledge base](knowledge-base.md#adding-a-signature).

### Can I use my own LLM provider or a local model?
Yes. Register a custom provider with `register_provider()`, or point the built-in Ollama adapter at
a local model for fully private enrichment. See [Plugin guide](plugin-guide.md) and
[AI providers](ai-providers.md).

### Does enrichment send my logs to a vendor?
Only if you enable it. When `enrich=True` and a provider is configured, a bounded slice of input is
sent to that provider. Keep it off, or use local Ollama, to avoid any egress. See
[Security](security.md).

### What happens if an LLM call fails?
The engine logs a warning and returns the deterministic result. Analysis is never broken by a
provider error.

### Is the output machine-readable?
Yes. Add `--json` on the CLI, or use the SDK/API to get the `AnalysisResult` model directly. See
[Output format](output-format.md).

### Is there a hosted version?
Yes — the [AI incident-response assistant](https://devopsaitoolkit.com/dashboard/incident-response)
offers a managed experience.

### How do I keep up with new signatures and features?
Subscribe at <https://devopsaitoolkit.com/newsletter> and watch the repository.

### What's the license?
MIT.

### What's on the roadmap?
A Web UI, VS Code extension, GitHub Action, MCP server, and Desktop app — all built on the same
engine. See the [Roadmap](roadmap.md).
