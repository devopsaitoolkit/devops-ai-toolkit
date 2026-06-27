"""Select the right analyzer for a given source kind / technology."""

from __future__ import annotations

from ..models.enums import SourceKind, Technology
from .base import Analyzer
from .manifest import ManifestAnalyzer
from .terraform import TerraformAnalyzer


def get_analyzer(source_kind: SourceKind, technology: Technology) -> Analyzer | None:
    """Return a structural analyzer for the input, or None when not applicable.

    Logs and command output have no structural analyzer (their value comes purely
    from signature matching), so this returns None for them.
    """
    if source_kind is SourceKind.TERRAFORM or technology is Technology.TERRAFORM:
        return TerraformAnalyzer()
    if source_kind is SourceKind.KUBERNETES_MANIFEST or technology in (
        Technology.KUBERNETES,
        Technology.OPENSHIFT,
    ):
        return ManifestAnalyzer(kubernetes=True)
    if source_kind in (SourceKind.YAML, SourceKind.COMPOSE):
        return ManifestAnalyzer(kubernetes=False)
    return None
