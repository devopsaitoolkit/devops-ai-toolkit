"""Anthropic (Claude) provider adapter using the Messages API."""

from __future__ import annotations

from ..utils.config import Settings, get_settings
from ._http import post_json
from .base import CompletionRequest

_API_URL = "https://api.anthropic.com/v1/messages"
_API_VERSION = "2023-06-01"


class AnthropicProvider:
    """Adapter for Anthropic Claude models via the public Messages API."""

    name = "anthropic"

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialise from resolved settings (reads ``ANTHROPIC_API_KEY``)."""
        self._settings = settings or get_settings()
        self.model = self._settings.anthropic_model

    def available(self) -> bool:
        """True when an Anthropic API key is present."""
        return bool(self._settings.anthropic_api_key)

    def complete(self, request: CompletionRequest) -> str:
        """Return Claude's completion for ``request``."""
        if not self.available():
            raise RuntimeError("ANTHROPIC_API_KEY is not set.")
        headers = {
            "x-api-key": self._settings.anthropic_api_key or "",
            "anthropic-version": _API_VERSION,
            "content-type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system": request.system,
            "messages": [{"role": "user", "content": request.prompt}],
        }
        data = post_json(
            _API_URL, headers=headers, payload=payload, timeout=self._settings.request_timeout
        )
        blocks = data.get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
