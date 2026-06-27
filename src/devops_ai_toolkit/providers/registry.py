"""Runtime registry that resolves a provider name to an adapter instance.

AI/LLM providers are a plugin point: the built-in adapters are registered here,
and third parties can add new backends either by calling :func:`register_provider`
or by advertising a ``devops_ai_toolkit.llm_providers`` entry point. The engine
depends only on the provider interface, so switching providers is configuration
only — no business-logic change.
"""

from __future__ import annotations

from collections.abc import Callable
from importlib import metadata as importlib_metadata

from ..utils.config import Settings, get_settings
from ..utils.logging import get_logger
from .anthropic import AnthropicProvider
from .azure_openai import AzureOpenAIProvider
from .base import AIProvider, NullProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider

_logger = get_logger(__name__)
ENTRY_POINT_GROUP = "devops_ai_toolkit.llm_providers"

# Factory functions keep construction lazy and let callers inject settings.
_FACTORIES: dict[str, Callable[[Settings], AIProvider]] = {
    "null": lambda _settings: NullProvider(),
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "azure_openai": AzureOpenAIProvider,
    "ollama": OllamaProvider,
}

_entrypoints_loaded = False


def register_provider(name: str, factory: Callable[[Settings], AIProvider]) -> None:
    """Register a custom provider factory under ``name``.

    Enables third parties to plug in additional LLM backends without modifying
    the toolkit, fulfilling the adapter-extensibility design goal.
    """
    _FACTORIES[name.lower()] = factory


def _load_entrypoint_providers() -> None:
    """Discover third-party providers advertised via entry points (once)."""
    global _entrypoints_loaded
    if _entrypoints_loaded:
        return
    _entrypoints_loaded = True
    try:
        entry_points = importlib_metadata.entry_points(group=ENTRY_POINT_GROUP)
    except TypeError:  # pragma: no cover - very old importlib.metadata
        entry_points = importlib_metadata.entry_points().get(ENTRY_POINT_GROUP, [])  # type: ignore[attr-defined]
    for entry_point in entry_points:
        try:
            factory = entry_point.load()
            register_provider(entry_point.name, factory)
        except Exception as exc:
            _logger.warning("Failed to load LLM provider %r: %s", entry_point.name, exc)


def available_providers() -> list[str]:
    """Return the names of all registered providers (including entry points)."""
    _load_entrypoint_providers()
    return sorted(_FACTORIES)


def get_provider(name: str | None = None, settings: Settings | None = None) -> AIProvider:
    """Resolve a provider by ``name`` (defaults to the configured provider).

    Unknown names fall back to the offline :class:`NullProvider` so the engine
    degrades gracefully instead of raising.
    """
    _load_entrypoint_providers()
    settings = settings or get_settings()
    key = (name or settings.provider or "null").lower()
    factory = _FACTORIES.get(key, _FACTORIES["null"])
    return factory(settings)
