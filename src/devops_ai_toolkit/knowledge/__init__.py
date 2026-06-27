"""The packaged knowledge base of DevOps error signatures."""

from __future__ import annotations

from .loader import KnowledgeBase, load_default_knowledge_base

__all__ = ["KnowledgeBase", "load_default_knowledge_base"]
