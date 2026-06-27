# AI providers

LLM providers are **optional enrichment**. The deterministic engine works fully offline; providers
only add a narrative and extra hypotheses on top of the knowledge-base findings when you ask for
them with `--enrich` / `enrich=True`.

The design goal is **vendor independence**: the core engine never imports a vendor SDK directly.
It depends only on the `AIProvider` protocol, and concrete adapters are resolved at runtime from a
registry.

## The adapter model

```python
from typing import Protocol, runtime_checkable
from dataclasses import dataclass

@dataclass(frozen=True)
class CompletionRequest:
    system: str
    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.2

@runtime_checkable
class AIProvider(Protocol):
    name: str
    model: str
    def available(self) -> bool: ...
    def complete(self, request: CompletionRequest) -> str: ...
```

Two rules every adapter follows:

1. **Construct safely even when unconfigured.** Never raise at import or `__init__`; report
   readiness through `available()` instead.
2. **Fail loud only in `complete()`.** If a key is missing or the network fails, raise a
   `RuntimeError` there. The engine catches it and falls back to deterministic results.

The default `NullProvider` is always "unavailable", which is what keeps the toolkit offline by
default.

## Built-in providers

| Name        | Backend                              | Configured by                          |
|-------------|--------------------------------------|----------------------------------------|
| `null`      | None (offline, deterministic)        | default                                |
| `anthropic` | Anthropic Claude (Messages API)      | `ANTHROPIC_API_KEY`                    |
| `openai`    | OpenAI chat completions              | `OPENAI_API_KEY` (+ `OPENAI_BASE_URL`) |
| `gemini`    | Google Gemini                        | `GEMINI_API_KEY` / `GOOGLE_API_KEY`    |
| `ollama`    | Local Ollama server                  | `OLLAMA_HOST`                          |

Adapters talk to vendors over plain HTTP (`requests`) — there's no required vendor SDK dependency.
See [Configuration](configuration.md) for the full variable list and model overrides.

## Selecting a provider

By environment:

```bash
export DEVOPS_AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
devops-ai analyze app.log --enrich
```

Per-invocation on the CLI:

```bash
devops-ai analyze app.log --enrich --provider openai
```

In Python, inject the provider:

```python
from devops_ai_toolkit import AnalysisEngine
from devops_ai_toolkit.providers.registry import get_provider

engine = AnalysisEngine(provider=get_provider("gemini"))
result = engine.analyze_file("app.log", enrich=True)
```

## How enrichment runs

When `enrich=True` and the resolved provider's `available()` is `True`, the engine:

1. Builds an enrichment prompt from the deterministic `AnalysisResult` plus a slice of the raw
   input.
2. Calls `provider.complete(...)` with a fixed system prompt and low temperature.
3. Splits the reply into a `narrative` and any `CAUSE:`-prefixed extra hypotheses.
4. Attaches them as `result.enrichment` (provider name, model, narrative, additional causes).

If the provider is unavailable, enrichment is skipped with a low-severity warning. If the call
fails (network/provider error), the engine logs it and returns the deterministic result unchanged —
**analysis is never broken by an LLM failure.**

```python
result = engine.analyze_file("app.log", enrich=True)
if result.enrichment:
    print(result.enrichment.narrative)
    for hypothesis in result.enrichment.additional_causes:
        print("extra:", hypothesis)
```

## Registry API

```python
from devops_ai_toolkit.providers.registry import (
    available_providers, get_provider, register_provider,
)

available_providers()        # ['anthropic', 'gemini', 'null', 'ollama', 'openai']
get_provider("anthropic")    # resolve a provider instance
get_provider()               # resolve the configured provider (or null)
```

Unknown names fall back to the offline `NullProvider` so the engine degrades gracefully instead of
raising.

## Adding your own provider

Register a factory under a name. The factory takes resolved `Settings` and returns anything that
satisfies the `AIProvider` protocol:

```python
from devops_ai_toolkit.providers.base import CompletionRequest
from devops_ai_toolkit.providers.registry import register_provider
from devops_ai_toolkit.utils.config import Settings

class MyProvider:
    name = "myllm"

    def __init__(self, settings: Settings) -> None:
        self.model = settings.extra.get("myllm_model", "my-default")
        self._endpoint = settings.extra.get("myllm_endpoint", "http://localhost:9000")

    def available(self) -> bool:
        return bool(self._endpoint)

    def complete(self, request: CompletionRequest) -> str:
        # call your backend over HTTP and return the text
        ...

register_provider("myllm", MyProvider)
```

Then select it:

```bash
export DEVOPS_AI_PROVIDER=myllm
devops-ai analyze app.log --enrich
```

A complete, runnable example is in the [Plugin guide](plugin-guide.md).

## See also

- [Configuration](configuration.md) — keys, models, endpoints
- [Security](security.md) — how API keys are handled
- Prefer not to manage keys yourself? Use the hosted
  [AI incident assistant](https://devopsaitoolkit.com/dashboard/incident-response).
