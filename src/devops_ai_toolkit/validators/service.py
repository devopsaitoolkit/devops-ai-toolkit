"""Dispatch manifest validation to the right validator based on content."""

from __future__ import annotations

from ..models.analysis import ValidationResult
from ..models.enums import SourceKind, Technology
from ..utils.text import detect_source_kind, detect_technology
from .kubernetes import validate_kubernetes
from .terraform import validate_terraform
from .yaml_validator import validate_yaml


def validate_manifest(
    text: str,
    *,
    technology: Technology | None = None,
    source_kind: SourceKind | None = None,
    filename: str | None = None,
) -> ValidationResult:
    """Validate ``text`` using the most specific validator available.

    Resolution order: explicit ``source_kind`` hint, then detected kind. Falls
    back to generic YAML validation.
    """
    kind = source_kind or detect_source_kind(text, filename)
    tech = technology or detect_technology(text, filename)

    if kind is SourceKind.TERRAFORM or tech is Technology.TERRAFORM:
        return validate_terraform(text)
    if kind is SourceKind.KUBERNETES_MANIFEST or tech in (
        Technology.KUBERNETES,
        Technology.OPENSHIFT,
    ):
        return validate_kubernetes(text)
    return validate_yaml(text)
