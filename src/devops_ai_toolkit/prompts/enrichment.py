"""Prompt construction for LLM enrichment of analysis results."""

from __future__ import annotations

from ..models.analysis import AnalysisResult
from ..utils.text import truncate

ENRICHMENT_SYSTEM_PROMPT = (
    "You are a senior Site Reliability Engineer assisting with READ-ONLY incident "
    "triage. You never suggest commands that mutate infrastructure (no apply, "
    "delete, restart, scale, or write operations). You explain clearly, cite the "
    "evidence you were given, and you are explicit about uncertainty. Keep the "
    "response concise and actionable."
)


def build_enrichment_prompt(result: AnalysisResult, raw_input: str, max_chars: int) -> str:
    """Build the user prompt that asks an LLM to enrich ``result``.

    The prompt includes the deterministic findings and a bounded slice of the raw
    input so the model grounds its narrative in real evidence.
    """
    causes = (
        "\n".join(
            f"- {rc.title} ({rc.confidence_percent}%): {rc.description}"
            for rc in result.root_causes
        )
        or "- (no signature matched; reason from the raw input)"
    )

    return (
        f"Technology: {result.technology}\n"
        f"Input kind: {result.source_kind}\n\n"
        f"Deterministic findings already produced by a rule engine:\n{causes}\n\n"
        f"Raw input (truncated):\n```\n{truncate(raw_input, max_chars)}\n```\n\n"
        "Tasks:\n"
        "1. Write a short narrative (3-5 sentences) explaining what is most likely "
        "happening and why, grounded in the evidence above.\n"
        "2. List up to 3 ADDITIONAL plausible root causes the rule engine may have "
        "missed, each on its own line prefixed with 'CAUSE:'.\n"
        "Do not propose any command that changes state."
    )
