"""Google Gemini provider adapter via the Generative Language API."""

from __future__ import annotations

from ..utils.config import Settings, get_settings
from ._http import post_json
from .base import CompletionRequest

_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiProvider:
    """Adapter for Google Gemini models."""

    name = "gemini"

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialise from resolved settings (reads ``GEMINI_API_KEY``)."""
        self._settings = settings or get_settings()
        self.model = self._settings.gemini_model

    def available(self) -> bool:
        """True when a Gemini/Google API key is present."""
        return bool(self._settings.gemini_api_key)

    def complete(self, request: CompletionRequest) -> str:
        """Return Gemini's completion for ``request``."""
        if not self.available():
            raise RuntimeError("GEMINI_API_KEY is not set.")
        url = f"{_BASE}/{self.model}:generateContent?key={self._settings.gemini_api_key}"
        payload = {
            "systemInstruction": {"parts": [{"text": request.system}]},
            "contents": [{"role": "user", "parts": [{"text": request.prompt}]}],
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature,
            },
        }
        data = post_json(
            url,
            headers={"Content-Type": "application/json"},
            payload=payload,
            timeout=self._settings.request_timeout,
        )
        candidates = data.get("candidates", [])
        if not candidates:
            return ""
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()
