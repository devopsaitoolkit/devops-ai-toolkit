"""Tests for the Azure OpenAI provider adapter and provider registry."""

from __future__ import annotations

import pytest

from devops_ai_toolkit.providers.azure_openai import AzureOpenAIProvider
from devops_ai_toolkit.providers.base import CompletionRequest
from devops_ai_toolkit.providers.registry import available_providers
from devops_ai_toolkit.utils.config import Settings


def test_keyless_provider_unavailable() -> None:
    provider = AzureOpenAIProvider(Settings(provider="azure_openai"))
    assert provider.name == "azure_openai"
    assert provider.available() is False


def test_complete_raises_when_unavailable() -> None:
    provider = AzureOpenAIProvider(Settings())
    request = CompletionRequest(system="sys", prompt="hello")
    with pytest.raises(RuntimeError):
        provider.complete(request)


def test_endpoint_alone_is_not_available() -> None:
    provider = AzureOpenAIProvider(
        Settings(azure_openai_endpoint="https://example.openai.azure.com")
    )
    assert provider.available() is False


def test_registry_includes_azure_openai() -> None:
    assert "azure_openai" in available_providers()
