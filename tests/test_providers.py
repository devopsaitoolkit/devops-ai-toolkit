"""Tests for providers and the provider registry. No network calls are made."""

from __future__ import annotations

import pytest

from devops_ai_toolkit.providers.anthropic import AnthropicProvider
from devops_ai_toolkit.providers.base import (
    AIProvider,
    CompletionRequest,
    NullProvider,
)
from devops_ai_toolkit.providers.gemini import GeminiProvider
from devops_ai_toolkit.providers.openai import OpenAIProvider
from devops_ai_toolkit.providers.registry import (
    available_providers,
    get_provider,
    register_provider,
)
from devops_ai_toolkit.utils.config import Settings


@pytest.fixture
def keyless_settings() -> Settings:
    """Settings with no API keys whatsoever."""
    return Settings(provider="null")


class TestNullProvider:
    def test_not_available(self):
        assert NullProvider().available() is False

    def test_complete_raises(self):
        with pytest.raises(RuntimeError, match="No AI provider configured"):
            NullProvider().complete(CompletionRequest(system="s", prompt="p"))

    def test_satisfies_protocol(self):
        assert isinstance(NullProvider(), AIProvider)


class TestRegistry:
    def test_unknown_name_returns_null(self, keyless_settings):
        provider = get_provider("not-a-real-provider", settings=keyless_settings)
        assert isinstance(provider, NullProvider)

    def test_explicit_null(self, keyless_settings):
        assert isinstance(get_provider("null", settings=keyless_settings), NullProvider)

    def test_default_falls_back_to_null(self, keyless_settings):
        # settings.provider == "null" with no name -> NullProvider.
        assert isinstance(get_provider(settings=keyless_settings), NullProvider)

    def test_known_names_resolve(self, keyless_settings):
        assert isinstance(get_provider("anthropic", settings=keyless_settings), AnthropicProvider)
        assert isinstance(get_provider("openai", settings=keyless_settings), OpenAIProvider)
        assert isinstance(get_provider("gemini", settings=keyless_settings), GeminiProvider)

    def test_case_insensitive(self, keyless_settings):
        assert isinstance(get_provider("ANTHROPIC", settings=keyless_settings), AnthropicProvider)

    def test_available_providers_lists_builtins(self):
        names = available_providers()
        for expected in ("null", "anthropic", "openai", "gemini", "ollama"):
            assert expected in names

    def test_register_provider(self, keyless_settings):
        class CustomProvider:
            name = "custom-test"
            model = "custom-model"

            def __init__(self, settings):
                self.settings = settings

            def available(self) -> bool:
                return False

            def complete(self, request):  # pragma: no cover - not invoked
                raise RuntimeError("nope")

        register_provider("custom-test", CustomProvider)
        assert "custom-test" in available_providers()
        provider = get_provider("custom-test", settings=keyless_settings)
        assert isinstance(provider, CustomProvider)
        assert provider.settings is keyless_settings


class TestAdaptersUnavailableWithoutKeys:
    def test_anthropic_unavailable(self, keyless_settings):
        provider = AnthropicProvider(settings=keyless_settings)
        assert provider.available() is False
        assert provider.name == "anthropic"
        assert provider.model == keyless_settings.anthropic_model

    def test_openai_unavailable(self, keyless_settings):
        provider = OpenAIProvider(settings=keyless_settings)
        assert provider.available() is False

    def test_gemini_unavailable(self, keyless_settings):
        provider = GeminiProvider(settings=keyless_settings)
        assert provider.available() is False

    def test_anthropic_complete_raises_without_key(self, keyless_settings):
        provider = AnthropicProvider(settings=keyless_settings)
        with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
            provider.complete(CompletionRequest(system="s", prompt="p"))

    def test_openai_complete_raises_without_key(self, keyless_settings):
        provider = OpenAIProvider(settings=keyless_settings)
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
            provider.complete(CompletionRequest(system="s", prompt="p"))

    def test_gemini_complete_raises_without_key(self, keyless_settings):
        provider = GeminiProvider(settings=keyless_settings)
        with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
            provider.complete(CompletionRequest(system="s", prompt="p"))


class TestAdaptersAvailableWithKeys:
    def test_anthropic_available_with_key(self):
        provider = AnthropicProvider(settings=Settings(anthropic_api_key="sk-test"))
        assert provider.available() is True

    def test_openai_available_with_key(self):
        provider = OpenAIProvider(settings=Settings(openai_api_key="sk-test"))
        assert provider.available() is True
