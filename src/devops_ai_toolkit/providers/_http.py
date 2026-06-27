"""Shared HTTP helper for provider adapters.

Adapters use :mod:`requests` (a declared dependency) rather than each vendor SDK,
keeping the dependency surface small and the provider layer uniform.
"""

from __future__ import annotations

from typing import Any

import requests


def post_json(
    url: str,
    *,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    """POST ``payload`` as JSON and return the parsed JSON response.

    Raises :class:`RuntimeError` with a readable message on HTTP or transport
    errors so callers do not need to handle ``requests`` exceptions directly.
    """
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as exc:  # network / DNS / timeout
        raise RuntimeError(f"AI provider request failed: {exc}") from exc

    if response.status_code >= 400:
        detail = response.text[:500]
        raise RuntimeError(f"AI provider returned HTTP {response.status_code}: {detail}")

    return response.json()
