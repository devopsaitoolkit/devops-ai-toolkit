"""A minimal, dependency-free Terraform/HCL reader.

This is intentionally a *lightweight* structural reader, not a full HCL2 parser.
It extracts resource/provider/variable blocks and flags obvious balance issues so
the engine can give useful, read-only feedback without a heavy native dependency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_BLOCK_RE = re.compile(
    r"(?P<kind>resource|data|provider|variable|module|output)\s+"
    r'"(?P<type>[^"]+)"(?:\s+"(?P<name>[^"]+)")?\s*\{',
    re.MULTILINE,
)


@dataclass
class TerraformResource:
    """A single declared Terraform block."""

    kind: str
    type: str
    name: str = ""
    line: int = 0


@dataclass
class ParsedTerraform:
    """The outcome of reading a Terraform configuration."""

    blocks: list[TerraformResource] = field(default_factory=list)
    brace_balanced: bool = True
    quote_balanced: bool = True

    @property
    def resources(self) -> list[TerraformResource]:
        """Only the ``resource`` blocks."""
        return [b for b in self.blocks if b.kind == "resource"]


def parse_terraform(text: str) -> ParsedTerraform:
    """Extract blocks and basic balance signals from Terraform ``text``."""
    blocks: list[TerraformResource] = []
    for match in _BLOCK_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        blocks.append(
            TerraformResource(
                kind=match.group("kind"),
                type=match.group("type"),
                name=match.group("name") or "",
                line=line,
            )
        )

    stripped = _strip_strings_and_comments(text)
    brace_balanced = stripped.count("{") == stripped.count("}")
    quote_balanced = text.count('"') % 2 == 0
    return ParsedTerraform(
        blocks=blocks, brace_balanced=brace_balanced, quote_balanced=quote_balanced
    )


def _strip_strings_and_comments(text: str) -> str:
    """Remove strings and comments so brace counting is not fooled by literals."""
    text = re.sub(r"#.*", "", text)
    text = re.sub(r"//.*", "", text)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)
