"""Prompt builders for optional LLM enrichment.

Enrichment is layered *on top of* deterministic findings: the model is given the
matched signatures and asked to add narrative and any additional hypotheses,
never to replace the rule-based output.
"""

from __future__ import annotations

from .enrichment import ENRICHMENT_SYSTEM_PROMPT, build_enrichment_prompt

__all__ = ["ENRICHMENT_SYSTEM_PROMPT", "build_enrichment_prompt"]
