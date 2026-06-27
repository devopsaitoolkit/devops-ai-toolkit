"""Read-only parsers that turn raw text into lightweight structured data."""

from __future__ import annotations

from .terraform import TerraformResource, parse_terraform
from .yaml_docs import ParsedYAML, parse_yaml_documents

__all__ = [
    "ParsedYAML",
    "TerraformResource",
    "parse_terraform",
    "parse_yaml_documents",
]
