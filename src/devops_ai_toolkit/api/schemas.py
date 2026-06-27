"""Request/response schemas for the REST API.

Responses reuse the canonical result models from
:mod:`devops_ai_toolkit.models`, so the API contract and the SDK contract never
drift apart.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..models.enums import SourceKind, Technology


class AnalyzeBody(BaseModel):
    """Body for the analyze endpoints."""

    content: str = Field(..., description="Raw text to analyze.", min_length=1)
    technology: Technology | None = Field(default=None, description="Optional technology hint.")
    source_kind: SourceKind | None = Field(default=None, description="Optional input-shape hint.")
    filename: str | None = Field(default=None)
    enrich: bool = Field(
        default=False, description="Add LLM narrative if a provider is configured."
    )
    max_root_causes: int = Field(default=5, ge=1, le=20)


class ExplainBody(BaseModel):
    """Body for the explain endpoint."""

    error: str = Field(..., description="Error name or message.", min_length=1)


class ValidateBody(BaseModel):
    """Body for the validate endpoint."""

    content: str = Field(..., min_length=1)
    technology: Technology | None = None
    source_kind: SourceKind | None = None
    filename: str | None = None


class HealthResponse(BaseModel):
    """Response for the health endpoint."""

    status: str = "ok"
    signatures: int
    provider: str
    provider_available: bool


class VersionResponse(BaseModel):
    """Response for the version endpoint."""

    name: str = "devops-ai-toolkit"
    version: str
