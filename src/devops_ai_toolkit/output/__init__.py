"""Rendering of results for humans (Rich) and machines (JSON)."""

from __future__ import annotations

from .console import render_analysis, render_explanation, render_validation
from .serialize import to_json

__all__ = ["render_analysis", "render_explanation", "render_validation", "to_json"]
