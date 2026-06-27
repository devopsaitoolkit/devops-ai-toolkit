"""Runtime configuration, sourced from the environment.

Settings are intentionally dependency-light (no pydantic-settings requirement)
so the core stays importable in minimal environments. All values have safe
defaults; nothing here is required for offline, deterministic analysis.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    """Resolved configuration for the engine and its optional AI providers."""

    provider: str = "null"
    """Active AI provider: 'null' (offline, default), 'anthropic', 'openai', 'gemini', 'ollama'."""

    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"

    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"

    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    request_timeout: int = 60
    max_input_chars: int = 200_000
    extra: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls, environ: dict[str, str] | None = None) -> Settings:
        """Build settings from environment variables (``DEVOPS_AI_*`` and vendor keys)."""
        env = environ if environ is not None else dict(os.environ)

        def get(*names: str, default: str | None = None) -> str | None:
            for name in names:
                if env.get(name):
                    return env[name]
            return default

        return cls(
            provider=get("DEVOPS_AI_PROVIDER", default="null") or "null",
            anthropic_api_key=get("ANTHROPIC_API_KEY", "DEVOPS_AI_ANTHROPIC_KEY"),
            anthropic_model=get("DEVOPS_AI_ANTHROPIC_MODEL", default="claude-sonnet-4-6")
            or "claude-sonnet-4-6",
            openai_api_key=get("OPENAI_API_KEY", "DEVOPS_AI_OPENAI_KEY"),
            openai_model=get("DEVOPS_AI_OPENAI_MODEL", default="gpt-4o-mini") or "gpt-4o-mini",
            openai_base_url=get("OPENAI_BASE_URL", default="https://api.openai.com/v1")
            or "https://api.openai.com/v1",
            gemini_api_key=get("GEMINI_API_KEY", "GOOGLE_API_KEY", "DEVOPS_AI_GEMINI_KEY"),
            gemini_model=get("DEVOPS_AI_GEMINI_MODEL", default="gemini-2.0-flash")
            or "gemini-2.0-flash",
            ollama_host=get("OLLAMA_HOST", default="http://localhost:11434")
            or "http://localhost:11434",
            ollama_model=get("DEVOPS_AI_OLLAMA_MODEL", default="llama3.1") or "llama3.1",
            request_timeout=int(get("DEVOPS_AI_TIMEOUT", default="60") or "60"),
            max_input_chars=int(get("DEVOPS_AI_MAX_CHARS", default="200000") or "200000"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return process-wide settings, resolved once from the environment."""
    return Settings.from_env()
