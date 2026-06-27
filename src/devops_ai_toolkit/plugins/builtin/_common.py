"""Helpers shared by built-in plugin modules."""

from __future__ import annotations

from ...knowledge.loader import load_default_knowledge_base
from ...models.enums import Technology
from ...models.knowledge import Signature
from ..knowledge_backed import KnowledgeBackedPlugin, Validator
from ..metadata import PluginMetadata


def signatures_for(*technologies: Technology) -> list[Signature]:
    """Return the packaged signatures owned by the given technologies.

    Built-in plugins partition the shared knowledge base by technology, so the
    YAML data stays the single source of truth and is never duplicated.
    """
    wanted = set(technologies)
    return [s for s in load_default_knowledge_base().signatures if s.technology in wanted]


def build(metadata: PluginMetadata, validator: Validator | None = None) -> KnowledgeBackedPlugin:
    """Construct a built-in plugin from its metadata and optional validator."""
    return KnowledgeBackedPlugin(
        metadata, signatures_for(*metadata.supported_technologies), validator
    )
