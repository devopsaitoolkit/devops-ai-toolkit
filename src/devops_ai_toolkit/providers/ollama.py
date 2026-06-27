"""Local Ollama provider adapter (offline / self-hosted LLMs)."""

from __future__ import annotations

import requests

from ..utils.config import Settings, get_settings
from ._http import post_json
from .base import CompletionRequest


class OllamaProvider:
    """Adapter for a locally running Ollama server."""

    name = "ollama"

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialise from resolved settings (reads ``OLLAMA_HOST``)."""
        self._settings = settings or get_settings()
        self.model = self._settings.ollama_model

    def available(self) -> bool:
        """True when the local Ollama server answers its version endpoint."""
        try:
            resp = requests.get(f"{self._settings.ollama_host.rstrip('/')}/api/version", timeout=2)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def complete(self, request: CompletionRequest) -> str:
        """Return the local model's completion for ``request``."""
        url = f"{self._settings.ollama_host.rstrip('/')}/api/chat"
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": request.temperature, "num_predict": request.max_tokens},
            "messages": [
                {"role": "system", "content": request.system},
                {"role": "user", "content": request.prompt},
            ],
        }
        data = post_json(
            url,
            headers={"Content-Type": "application/json"},
            payload=payload,
            timeout=self._settings.request_timeout,
        )
        return str(data.get("message", {}).get("content", "")).strip()
