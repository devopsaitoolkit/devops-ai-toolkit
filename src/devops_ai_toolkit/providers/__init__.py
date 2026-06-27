"""Pluggable AI / LLM provider adapters.

The core engine never imports a vendor SDK directly. It depends only on the
:class:`LLMProvider` (a.k.a. :class:`AIProvider`) protocol, and providers are
resolved at runtime via :func:`get_provider`. This keeps the toolkit usable fully
offline (the default :class:`NullProvider`) and lets contributors add new
backends as adapters — either with :func:`register_provider` or a
``devops_ai_toolkit.llm_providers`` entry point.
"""

from __future__ import annotations

from .anthropic import AnthropicProvider
from .azure_openai import AzureOpenAIProvider
from .base import AIProvider, CompletionRequest, LLMProvider, NullProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai import OpenAIProvider
from .registry import (
    ENTRY_POINT_GROUP,
    available_providers,
    get_provider,
    register_provider,
)

__all__ = [
    "ENTRY_POINT_GROUP",
    "AIProvider",
    "AnthropicProvider",
    "AzureOpenAIProvider",
    "CompletionRequest",
    "GeminiProvider",
    "LLMProvider",
    "NullProvider",
    "OllamaProvider",
    "OpenAIProvider",
    "available_providers",
    "get_provider",
    "register_provider",
]
