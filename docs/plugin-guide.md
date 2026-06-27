# Plugin guide

The toolkit is extensible in two ways without forking it: **custom AI providers** and **custom
signatures / knowledge bases**. Both are first-class, by design.

## 1. Custom AI providers

The engine depends only on the `AIProvider` protocol, and providers are resolved at runtime from a
registry. To add a backend, write an adapter and register a factory.

### The contract

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

Rules:

1. Constructing the provider must **never raise**, even when unconfigured.
2. Report readiness via `available()`.
3. Raise (`RuntimeError`) only inside `complete()` on missing config / network failure — the engine
   catches it and falls back to deterministic output.

### A complete example

```python
import requests
from devops_ai_toolkit.providers.base import CompletionRequest
from devops_ai_toolkit.providers.registry import register_provider
from devops_ai_toolkit.utils.config import Settings


class MyLLMProvider:
    """Adapter for an internal OpenAI-compatible gateway."""

    name = "myllm"

    def __init__(self, settings: Settings) -> None:
        # Use settings + the extra dict for custom config (no env coupling required).
        self._endpoint = settings.extra.get("myllm_endpoint", "http://localhost:9000/v1/complete")
        self._api_key = settings.extra.get("myllm_key", "")
        self._timeout = settings.request_timeout
        self.model = settings.extra.get("myllm_model", "my-default")

    def available(self) -> bool:
        return bool(self._endpoint and self._api_key)

    def complete(self, request: CompletionRequest) -> str:
        if not self.available():
            raise RuntimeError("MyLLM is not configured.")
        resp = requests.post(
            self._endpoint,
            headers={"authorization": f"Bearer {self._api_key}"},
            json={
                "model": self.model,
                "system": request.system,
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            },
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()["text"].strip()


# Register once at import time (e.g. in your app's startup module).
register_provider("myllm", MyLLMProvider)
```

Use it:

```python
from devops_ai_toolkit import AnalysisEngine
from devops_ai_toolkit.providers.registry import get_provider

engine = AnalysisEngine(provider=get_provider("myllm"))
result = engine.analyze_file("app.log", enrich=True)
```

Or select it via environment once registered: `DEVOPS_AI_PROVIDER=myllm`. See
[AI providers](ai-providers.md) and [Configuration](configuration.md).

> Tip: `register_provider` mutates a process-global registry. Register early (import side effect or
> app startup) and only once per name.

## 2. Custom signatures and knowledge bases

Signatures are declarative YAML — the lowest-effort way to teach the toolkit new errors. See the
full schema in [Knowledge base](knowledge-base.md).

### Add to the packaged catalog (for contribution)

Append a list item to a file under `src/devops_ai_toolkit/knowledge/data/` and open a PR. See
[Contributing](contributing.md).

### Ship a private knowledge base (in your own app)

Keep proprietary signatures out of the repo and load them at runtime:

```python
from devops_ai_toolkit import AnalysisEngine
from devops_ai_toolkit.knowledge.loader import KnowledgeBase

kb = KnowledgeBase.from_yaml_dir("/etc/devops-ai/signatures")
engine = AnalysisEngine(knowledge_base=kb)
result = engine.analyze_text("OUR-CUSTOM-ERROR-CODE 0x42")
```

A minimal signature file (`/etc/devops-ai/signatures/internal.yaml`):

```yaml
- id: acme.payments_timeout
  technology: linux
  title: "Payments service upstream timeout"
  summary: "The payments gateway exceeded its upstream deadline."
  applies_to: [log, error_string]
  match:
    any_of:
      - "upstream timed out.*payments"
      - "PAYMENTS_GATEWAY_DEADLINE_EXCEEDED"
    weight: 0.85
  root_causes:
    - title: "Downstream gateway slow or down"
      description: "The payments gateway is not responding within the deadline."
      confidence: 0.7
      category: network
  diagnostic_commands:
    - command: "curl -s -o /dev/null -w '%{http_code} %{time_total}\\n' https://gw.internal/health"
      explanation: "Read-only health/latency probe of the gateway."
  suggested_fixes:
    - title: "Check gateway health and circuit breaker"
      description: "Confirm the gateway is up and the breaker isn't open before raising timeouts."
  references:
    - title: "Internal runbook: payments timeouts"
      url: "https://runbooks.acme.internal/payments-timeout"
  tags: [payments, timeout]
```

Keep every diagnostic command **read-only** — that rule applies to custom signatures too. See
[Security](security.md).

### Combining both

A custom engine with both a private catalog and a custom provider:

```python
from devops_ai_toolkit import AnalysisEngine
from devops_ai_toolkit.knowledge.loader import KnowledgeBase
from devops_ai_toolkit.providers.registry import get_provider, register_provider

register_provider("myllm", MyLLMProvider)  # from above

engine = AnalysisEngine(
    knowledge_base=KnowledgeBase.from_yaml_dir("/etc/devops-ai/signatures"),
    provider=get_provider("myllm"),
)
```

## See also

- [Knowledge base](knowledge-base.md) — full signature schema
- [AI providers](ai-providers.md) — the adapter model
- [Testing guide](testing-guide.md) — how to test providers and signatures
