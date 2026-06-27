"""Runtime registry that resolves a provider name to an adapter instance."""

from __future__ import annotations

from collections.abc import Callable

from ..utils.config import Settings, get_settings
from .anthropic import AnthropicProvider
from .base import AIProvider, NullProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider

# Factory functions keep construction lazy and let callers inject settings.
_FACTORIES: dict[str, Callable[[Settings], AIProvider]] = {
    "null": lambda _settings: NullProvider(),
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}


def register_provider(name: str, factory: Callable[[Settings], AIProvider]) -> None:
    """Register a custom provider factory under ``name``.

    Enables third parties to plug in additional LLM backends without modifying
    the toolkit, fulfilling the adapter-extensibility design goal.
    """
    _FACTORIES[name.lower()] = factory


def available_providers() -> list[str]:
    """Return the names of all registered providers."""
    return sorted(_FACTORIES)


def get_provider(name: str | None = None, settings: Settings | None = None) -> AIProvider:
    """Resolve a provider by ``name`` (defaults to the configured provider).

    Unknown names fall back to the offline :class:`NullProvider` so the engine
    degrades gracefully instead of raising.
    """
    settings = settings or get_settings()
    key = (name or settings.provider or "null").lower()
    factory = _FACTORIES.get(key, _FACTORIES["null"])
    return factory(settings)
