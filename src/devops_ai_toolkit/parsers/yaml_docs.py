"""Parse one or many YAML documents, capturing syntax errors gracefully."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class ParsedYAML:
    """The outcome of parsing a YAML blob (possibly multi-document)."""

    documents: list[Any] = field(default_factory=list)
    error: str | None = None
    error_line: int | None = None

    @property
    def ok(self) -> bool:
        """True when the YAML parsed without a syntax error."""
        return self.error is None


def parse_yaml_documents(text: str) -> ParsedYAML:
    """Parse ``text`` as a stream of YAML documents.

    Returns a :class:`ParsedYAML` with the loaded documents, or a captured error
    message and 1-based line number when the YAML is malformed. Never raises.
    """
    try:
        docs = [doc for doc in yaml.safe_load_all(text) if doc is not None]
        return ParsedYAML(documents=docs)
    except yaml.YAMLError as exc:
        line: int | None = None
        mark = getattr(exc, "problem_mark", None)
        if mark is not None:
            line = mark.line + 1
        return ParsedYAML(error=str(exc).strip(), error_line=line)
