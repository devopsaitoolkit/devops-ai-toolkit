"""Load and index error signatures from packaged YAML data files.

Signatures are plain data (``knowledge/data/*.yaml``), so contributors expand
coverage by adding YAML — no engine changes required. The loader validates each
signature against the :class:`~devops_ai_toolkit.models.knowledge.Signature`
schema, surfacing malformed data files early.
"""

from __future__ import annotations

from collections.abc import Iterable
from functools import lru_cache
from importlib import resources
from pathlib import Path

import yaml

from ..models.enums import Technology
from ..models.knowledge import Signature

_DATA_PACKAGE = "devops_ai_toolkit.knowledge.data"


class KnowledgeBase:
    """An indexed, queryable collection of error signatures."""

    def __init__(self, signatures: Iterable[Signature]) -> None:
        """Build indexes by id and technology for fast lookup."""
        self._by_id: dict[str, Signature] = {}
        self._by_tech: dict[Technology, list[Signature]] = {}
        for sig in signatures:
            if sig.id in self._by_id:
                raise ValueError(f"duplicate signature id: {sig.id!r}")
            self._by_id[sig.id] = sig
            self._by_tech.setdefault(sig.technology, []).append(sig)

    def __len__(self) -> int:
        return len(self._by_id)

    @property
    def signatures(self) -> list[Signature]:
        """All signatures in the knowledge base."""
        return list(self._by_id.values())

    @property
    def technologies(self) -> list[Technology]:
        """Technologies that have at least one signature."""
        return sorted(self._by_tech, key=str)

    def get(self, signature_id: str) -> Signature | None:
        """Return a signature by id, or None."""
        return self._by_id.get(signature_id)

    def for_technology(self, technology: Technology) -> list[Signature]:
        """Return signatures scoped to ``technology``."""
        return list(self._by_tech.get(technology, []))

    def candidates(self, technology: Technology | None) -> list[Signature]:
        """Return the signatures worth evaluating for ``technology``.

        When the technology is unknown we evaluate everything; otherwise we scope
        to the matching technology to keep matching fast and precise.
        """
        if technology is None or technology is Technology.UNKNOWN:
            return self.signatures
        scoped = self.for_technology(technology)
        return scoped or self.signatures

    def search(self, query: str) -> list[Signature]:
        """Return signatures whose id/title/tags loosely match ``query``."""
        needle = query.lower().strip()
        hits: list[Signature] = []
        for sig in self._by_id.values():
            haystack = " ".join([sig.id, sig.title, sig.summary, *sig.tags]).lower()
            if needle in haystack:
                hits.append(sig)
        return hits


def _iter_signature_dicts() -> Iterable[dict[str, object]]:
    """Yield raw signature mappings from every packaged YAML data file."""
    data_root = resources.files(_DATA_PACKAGE)
    for entry in data_root.iterdir():
        if not entry.name.endswith((".yaml", ".yml")):
            continue
        content = entry.read_text(encoding="utf-8")
        loaded = yaml.safe_load(content) or []
        if isinstance(loaded, dict):
            loaded = loaded.get("signatures", [])
        for item in loaded:
            if isinstance(item, dict):
                yield item


def load_signatures_from_dir(directory: str | Path) -> list[Signature]:
    """Load and validate signatures from an arbitrary directory of YAML files."""
    signatures: list[Signature] = []
    for path in sorted(Path(directory).glob("*.y*ml")):
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        if isinstance(loaded, dict):
            loaded = loaded.get("signatures", [])
        for item in loaded:
            signatures.append(Signature.model_validate(item))
    return signatures


@lru_cache(maxsize=1)
def load_default_knowledge_base() -> KnowledgeBase:
    """Load, validate and cache the packaged knowledge base."""
    signatures = [Signature.model_validate(item) for item in _iter_signature_dicts()]
    return KnowledgeBase(signatures)
