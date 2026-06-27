"""Browse and enumerate the knowledge base of known errors.

The engine owns *matching*; this module owns *discovery* — listing what the
toolkit knows about, grouped by technology, for the CLI ``list`` command, the
REST ``GET /catalog`` endpoint and documentation generation.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..knowledge.loader import KnowledgeBase, load_default_knowledge_base
from ..models.enums import Technology


@dataclass(frozen=True)
class CatalogEntry:
    """A single browsable knowledge-base entry."""

    id: str
    technology: Technology
    title: str
    summary: str
    tags: tuple[str, ...]


class ErrorCatalog:
    """A read-only view over the knowledge base for discovery."""

    def __init__(self, knowledge_base: KnowledgeBase | None = None) -> None:
        """Bind to a knowledge base (defaults to the packaged one)."""
        self._kb = knowledge_base or load_default_knowledge_base()

    def entries(self, technology: Technology | None = None) -> list[CatalogEntry]:
        """Return catalog entries, optionally filtered by technology."""
        signatures = self._kb.for_technology(technology) if technology else self._kb.signatures
        return [
            CatalogEntry(
                id=s.id,
                technology=s.technology,
                title=s.title,
                summary=s.summary,
                tags=tuple(s.tags),
            )
            for s in sorted(signatures, key=lambda s: s.id)
        ]

    def grouped(self) -> dict[Technology, list[CatalogEntry]]:
        """Return catalog entries grouped by technology."""
        groups: dict[Technology, list[CatalogEntry]] = {}
        for entry in self.entries():
            groups.setdefault(entry.technology, []).append(entry)
        return groups

    def technologies(self) -> list[Technology]:
        """Technologies that have at least one catalogued error."""
        return self._kb.technologies

    def __len__(self) -> int:
        return len(self._kb)


__all__ = ["CatalogEntry", "ErrorCatalog"]
