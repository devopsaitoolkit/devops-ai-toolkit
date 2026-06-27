# LLM providers

The AI/LLM layer is **itself a plugin point**. The engine depends only on a small
provider *interface*, never on a vendor SDK, so switching providers is
**configuration only** — no business-logic change. By default the toolkit runs in
pure offline mode (the `null` provider); configuring a provider adds optional
narrative enrichment on top of the deterministic, signature-based analysis.

This mirrors the analyzer plugin model in [Plugins](plugins.md): a clean interface
plus an entry point means new backends drop in without touching the core.

---

## The provider interface

Defined in `devops_ai_toolkit.providers.base`. A provider is any object satisfying
the `LLMProvider` (aka `AIProvider`) `Protocol`:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class AIProvider(Protocol):
    name: str
    model: str

    def available(self) -> bool:
        """True when the provider is configured and usable."""

    def complete(self, request: CompletionRequest) -> str:
        """Return the model's text completion for the request."""

# Canonical public alias — the engine depends only on this Protocol.
LLMProvider = AIProvider
```

A `CompletionRequest` is a frozen dataclass: `system`, `prompt`,
`max_tokens` (default `1024`), `temperature` (default `0.2`).

Two rules make providers safe to plug in:

1. **Construct safely even when unconfigured** — never raise at import/init.
   Report readiness through `available()`.
2. **Degrade gracefully** — when no provider is configured, the default
   `NullProvider` reports `available() == False` and the engine runs in
   deterministic mode with no LLM calls.

---

## Built-in providers

Registered in `devops_ai_toolkit.providers.registry`. Select one with
`DEVOPS_AI_PROVIDER`; the default is `null` (offline).

| Provider | `DEVOPS_AI_PROVIDER` | Key / config env vars | Notes |
| --- | --- | --- | --- |
| Null (offline) | `null` *(default)* | none | Deterministic mode; no LLM calls. |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` (or `DEVOPS_AI_ANTHROPIC_KEY`); model via `DEVOPS_AI_ANTHROPIC_MODEL` | Default model `claude-sonnet-4-6`. |
| OpenAI | `openai` | `OPENAI_API_KEY` (or `DEVOPS_AI_OPENAI_KEY`); `OPENAI_BASE_URL`, `DEVOPS_AI_OPENAI_MODEL` | Default model `gpt-4o-mini`. |
| Gemini | `gemini` | `GEMINI_API_KEY` (or `GOOGLE_API_KEY` / `DEVOPS_AI_GEMINI_KEY`); `DEVOPS_AI_GEMINI_MODEL` | Default model `gemini-2.0-flash`. |
| Azure OpenAI | `azure_openai` | `AZURE_OPENAI_API_KEY` **and** `AZURE_OPENAI_ENDPOINT`; `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_API_VERSION` | Deployment-based; both key and endpoint required. |
| Ollama (local) | `ollama` | `OLLAMA_HOST` (default `http://localhost:11434`); `DEVOPS_AI_OLLAMA_MODEL` | Local models, no cloud key. Default model `llama3.1`. |

```bash
# Offline by default — nothing to set:
devops-ai analyze nova.log

# Enable Anthropic enrichment:
export DEVOPS_AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
devops-ai analyze nova.log

# Fully local with Ollama:
export DEVOPS_AI_PROVIDER=ollama
export OLLAMA_HOST=http://localhost:11434
devops-ai analyze nova.log
```

Unknown provider names fall back to `NullProvider`, so a typo degrades to offline
mode rather than raising. List the registered providers
(`registry.available_providers()`) to see what's available, including any added by
entry points.

---

## Adding a provider

There are two ways to add a backend, neither of which touches the core.

### 1. In-process registration

Call `register_provider(name, factory)` where `factory` is a callable taking
`Settings` and returning an `LLMProvider`:

```python
from devops_ai_toolkit.providers.registry import register_provider
from devops_ai_toolkit.providers.base import CompletionRequest

class MyProvider:
    name = "myllm"
    model = "my-model-1"

    def __init__(self, settings):
        self._key = settings.extra.get("MYLLM_API_KEY")

    def available(self) -> bool:
        return bool(self._key)

    def complete(self, request: CompletionRequest) -> str:
        ...  # call your backend, return text

register_provider("myllm", MyProvider)
# then: DEVOPS_AI_PROVIDER=myllm
```

### 2. Entry-point registration (packaged)

Advertise a **`devops_ai_toolkit.llm_providers`** entry point; the registry loads
it lazily and tolerates failures (a broken provider is logged and skipped, not
fatal). The entry point name becomes the provider name.

```toml
# pyproject.toml of your provider package
[project.entry-points."devops_ai_toolkit.llm_providers"]
myllm = "my_provider:MyProvider"     # a factory: Settings -> LLMProvider
```

```bash
pip install my-provider
export DEVOPS_AI_PROVIDER=myllm
devops-ai analyze nova.log
```

---

## Why switching is config-only

The engine calls only `available()` and `complete()` through the `LLMProvider`
Protocol — it has no knowledge of any vendor. Choosing a provider sets
`DEVOPS_AI_PROVIDER` (and the matching key); everything else — prompts, parsing,
result assembly — is identical across providers. That is the same adapter pattern
the analyzer plugins use: depend on the interface, discover implementations.

> See more on configuration in [Configuration](configuration.md) and the adapter
> model in [AI providers](ai-providers.md). Tutorials at
> <https://devopsaitoolkit.com>.

---

## See also

- [Plugins](plugins.md) — the analyzer plugin point this layer parallels.
- [AI providers](ai-providers.md) — the user-facing provider overview.
- [Configuration](configuration.md) — all environment variables.
- [Security](security.md) — key handling and the offline-first guarantee.
