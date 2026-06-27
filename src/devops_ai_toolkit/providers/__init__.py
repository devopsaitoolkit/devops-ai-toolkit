"""Pluggable AI provider adapters.

The core engine never imports a vendor SDK directly. It depends only on the
:class:`AIProvider` protocol, and providers are resolved at runtime via
:func:`get_provider`. This keeps the toolkit usable fully offline (the default
:class:`NullProvider`) and lets contributors add new backends as adapters.
"""

from __future__ import annotations

from .anthropic import AnthropicProvider
from .base import AIProvider, CompletionRequest, NullProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .registry import available_providers, get_provider, register_provider

__all__ = [
    "AIProvider",
    "AnthropicProvider",
    "CompletionRequest",
    "GeminiProvider",
    "NullProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "available_providers",
    "get_provider",
    "register_provider",
]
