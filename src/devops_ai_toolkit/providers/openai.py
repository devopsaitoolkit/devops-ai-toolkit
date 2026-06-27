"""OpenAI (and OpenAI-compatible) provider adapter via the Chat Completions API."""

from __future__ import annotations

from ..utils.config import Settings, get_settings
from ._http import post_json
from .base import CompletionRequest


class OpenAIProvider:
    """Adapter for OpenAI and any OpenAI-compatible endpoint (set ``OPENAI_BASE_URL``)."""

    name = "openai"

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialise from resolved settings (reads ``OPENAI_API_KEY``)."""
        self._settings = settings or get_settings()
        self.model = self._settings.openai_model

    def available(self) -> bool:
        """True when an OpenAI API key is present."""
        return bool(self._settings.openai_api_key)

    def complete(self, request: CompletionRequest) -> str:
        """Return the chat completion for ``request``."""
        if not self.available():
            raise RuntimeError("OPENAI_API_KEY is not set.")
        url = f"{self._settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.prompt},
            ],
        }
        data = post_json(
            url, headers=headers, payload=payload, timeout=self._settings.request_timeout
        )
        choices = data.get("choices", [])
        if not choices:
            return ""
        return str(choices[0].get("message", {}).get("content", "")).strip()
