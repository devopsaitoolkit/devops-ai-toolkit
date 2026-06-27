"""Analyzer that folds manifest validation into the analysis result."""

from __future__ import annotations

from ..models.analysis import AnalysisResult, Warning
from ..models.enums import Severity
from ..validators.kubernetes import validate_kubernetes
from ..validators.yaml_validator import validate_yaml


class ManifestAnalyzer:
    """Augment YAML/Kubernetes analyses with structural best-practice findings."""

    def __init__(self, *, kubernetes: bool) -> None:
        """Choose the kubernetes-aware validator when analyzing a manifest."""
        self._kubernetes = kubernetes

    def augment(self, result: AnalysisResult, content: str) -> AnalysisResult:
        """Run the appropriate validator and merge its findings into ``result``."""
        validation = validate_kubernetes(content) if self._kubernetes else validate_yaml(content)
        for issue in validation.issues:
            result.warnings.append(
                Warning(
                    message=(
                        f"{issue.message} {issue.hint}".strip()
                        + (f" ({issue.path})" if issue.path else "")
                    ),
                    severity=issue.severity if issue.severity != Severity.INFO else Severity.LOW,
                )
            )
        for tip in validation.best_practices:
            if tip not in result.best_practices:
                result.best_practices.append(tip)
        return result
