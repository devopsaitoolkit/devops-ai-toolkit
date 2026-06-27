"""The AI provider contract and the default offline provider."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class CompletionRequest:
    """A single text-completion request handed to a provider."""

    system: str
    prompt: str
    max_tokens: int = 1024
    temperature: float = 0.2


@runtime_checkable
class AIProvider(Protocol):
    """Minimal interface every AI backend must implement.

    Implementations must be safe to construct even when unconfigured; report
    readiness through :meth:`available` rather than raising at import/init time.
    """

    name: str
    model: str

    def available(self) -> bool:
        """Return True when the provider is configured and usable."""
        ...

    def complete(self, request: CompletionRequest) -> str:
        """Return the model's text completion for ``request``."""
        ...


# Canonical public name for the provider interface. The AI/LLM layer is itself a
# plugin point: the engine depends only on this Protocol, never on a vendor SDK.
LLMProvider = AIProvider


class NullProvider:
    """Default provider used when no AI backend is configured.

    It is always "unavailable", so the engine runs in pure deterministic mode.
    Calling :meth:`complete` raises, but the engine never does so unless a caller
    explicitly requests enrichment with a configured provider.
    """

    name = "null"
    model = "none"

    def available(self) -> bool:
        """The null provider is never available for enrichment."""
        return False

    def complete(self, request: CompletionRequest) -> str:
        """Raise: the null provider cannot produce completions."""
        raise RuntimeError(
            "No AI provider configured. Set DEVOPS_AI_PROVIDER and the matching API key "
            "to enable LLM enrichment, or run in the default offline mode."
        )
