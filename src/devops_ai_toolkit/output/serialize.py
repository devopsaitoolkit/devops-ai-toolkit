"""JSON serialization helpers for results."""

from __future__ import annotations

from pydantic import BaseModel


def to_json(model: BaseModel, *, indent: int = 2) -> str:
    """Serialize any result model to pretty JSON (including computed fields)."""
    return model.model_dump_json(indent=indent)
