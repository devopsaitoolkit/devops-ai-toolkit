"""Match input text against knowledge-base signatures and rank the hits."""

from __future__ import annotations

from ..knowledge.loader import KnowledgeBase
from ..models.enums import Technology
from ..models.knowledge import SignatureMatch


class SignatureMatcher:
    """Evaluate signatures against text and return ranked matches.

    Scoring combines a signature's declared ``weight`` with a small bonus for the
    number of distinct patterns it matched, so a signature that matches several
    independent signals outranks one that matched on a single weak token.
    """

    def __init__(self, knowledge_base: KnowledgeBase) -> None:
        """Bind the matcher to a knowledge base."""
        self._kb = knowledge_base

    def match(
        self, text: str, technology: Technology | None = None, *, limit: int = 10
    ) -> list[SignatureMatch]:
        """Return ranked :class:`SignatureMatch` objects for ``text``."""
        matches: list[SignatureMatch] = []
        for signature in self._kb.candidates(technology):
            matched, evidence = signature.match.evaluate(text)
            if not matched:
                continue
            unique_evidence = _dedupe(evidence)
            bonus = min(0.1 * (len(unique_evidence) - 1), 0.2)
            score = min(signature.match.weight + bonus, 1.0)
            matches.append(
                SignatureMatch(signature=signature, score=score, evidence=unique_evidence)
            )

        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:limit]


def _dedupe(items: list[str]) -> list[str]:
    """Return items with order preserved and duplicates/empties removed."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out
