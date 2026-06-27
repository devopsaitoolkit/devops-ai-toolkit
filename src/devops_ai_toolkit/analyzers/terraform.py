"""Analyzer that folds Terraform validation into the analysis result."""

from __future__ import annotations

from ..models.analysis import AnalysisResult, Warning
from ..validators.terraform import validate_terraform


class TerraformAnalyzer:
    """Augment Terraform analyses with static structural findings."""

    def augment(self, result: AnalysisResult, content: str) -> AnalysisResult:
        """Run the Terraform validator and merge its findings into ``result``."""
        validation = validate_terraform(content)
        for issue in validation.issues:
            result.warnings.append(
                Warning(message=f"{issue.message} {issue.hint}".strip(), severity=issue.severity)
            )
        for tip in validation.best_practices:
            if tip not in result.best_practices:
                result.best_practices.append(tip)
        return result
