"""Azure OpenAI provider adapter via the Chat Completions API."""

from __future__ import annotations

from ..utils.config import Settings, get_settings
from ._http import post_json
from .base import CompletionRequest


class AzureOpenAIProvider:
    """Adapter for Azure OpenAI deployments."""

    name = "azure_openai"

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialise from resolved settings (reads ``AZURE_OPENAI_*``)."""
        self._settings = settings or get_settings()
        self.model = self._settings.azure_openai_deployment

    def available(self) -> bool:
        """True when an Azure OpenAI key and endpoint are configured."""
        return bool(self._settings.azure_openai_api_key and self._settings.azure_openai_endpoint)

    def complete(self, request: CompletionRequest) -> str:
        """Return the deployment's chat completion for ``request``."""
        if not self.available():
            raise RuntimeError("AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT must be set.")
        endpoint = (self._settings.azure_openai_endpoint or "").rstrip("/")
        url = (
            f"{endpoint}/openai/deployments/{self._settings.azure_openai_deployment}"
            f"/chat/completions?api-version={self._settings.azure_openai_api_version}"
        )
        headers = {
            "api-key": self._settings.azure_openai_api_key or "",
            "Content-Type": "application/json",
        }
        payload = {
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
