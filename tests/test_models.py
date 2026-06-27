"""Tests for the pydantic models: computed fields and validation bounds."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from devops_ai_toolkit.models.analysis import (
    AnalysisRequest,
    AnalysisResult,
    RootCause,
    ValidationIssue,
    ValidationResult,
)
from devops_ai_toolkit.models.enums import (
    ConfidenceBand,
    Severity,
    SourceKind,
    Technology,
)


def _root_cause(confidence: float, title: str = "c") -> RootCause:
    return RootCause(title=title, description="desc", confidence=confidence)


class TestRootCause:
    def test_confidence_percent_rounds(self):
        assert _root_cause(0.0).confidence_percent == 0
        assert _root_cause(1.0).confidence_percent == 100
        assert _root_cause(0.666).confidence_percent == 67
        assert _root_cause(0.834).confidence_percent == 83

    @pytest.mark.parametrize(
        "score,band",
        [
            (0.0, ConfidenceBand.VERY_LOW),
            (0.24, ConfidenceBand.VERY_LOW),
            (0.25, ConfidenceBand.LOW),
            (0.44, ConfidenceBand.LOW),
            (0.45, ConfidenceBand.MODERATE),
            (0.64, ConfidenceBand.MODERATE),
            (0.65, ConfidenceBand.HIGH),
            (0.84, ConfidenceBand.HIGH),
            (0.85, ConfidenceBand.VERY_HIGH),
            (1.0, ConfidenceBand.VERY_HIGH),
        ],
    )
    def test_confidence_band(self, score, band):
        assert _root_cause(score).confidence_band is band

    def test_confidence_bounds(self):
        with pytest.raises(ValidationError):
            _root_cause(-0.1)
        with pytest.raises(ValidationError):
            _root_cause(1.1)

    def test_evidence_defaults_empty(self):
        assert _root_cause(0.5).evidence == []
        assert _root_cause(0.5).category == "general"


class TestConfidenceBandFromScore:
    def test_boundary_values(self):
        assert ConfidenceBand.from_score(0.85) is ConfidenceBand.VERY_HIGH
        assert ConfidenceBand.from_score(0.849999) is ConfidenceBand.HIGH


class TestAnalysisResultComputed:
    def test_confidence_is_max_root_cause(self):
        result = AnalysisResult(
            summary="s",
            technology=Technology.KUBERNETES,
            source_kind=SourceKind.LOG,
            root_causes=[_root_cause(0.4), _root_cause(0.9), _root_cause(0.6)],
        )
        assert result.confidence == 0.9
        assert result.confidence_percent == 90
        assert result.matched is True

    def test_no_root_causes(self):
        result = AnalysisResult(
            summary="s",
            technology=Technology.UNKNOWN,
            source_kind=SourceKind.LOG,
        )
        assert result.confidence == 0.0
        assert result.confidence_percent == 0
        assert result.matched is False

    def test_defaults_are_empty_collections(self):
        result = AnalysisResult(
            summary="s",
            technology=Technology.UNKNOWN,
            source_kind=SourceKind.LOG,
        )
        assert result.diagnostic_commands == []
        assert result.warnings == []
        assert result.enrichment is None
        assert result.metadata == {}


class TestAnalysisRequest:
    def test_defaults(self):
        req = AnalysisRequest(content="hi")
        assert req.technology is None
        assert req.source_kind is None
        assert req.enrich is False
        assert req.max_root_causes == 5

    def test_max_root_causes_bounds(self):
        with pytest.raises(ValidationError):
            AnalysisRequest(content="x", max_root_causes=0)
        with pytest.raises(ValidationError):
            AnalysisRequest(content="x", max_root_causes=21)
        # boundaries accepted
        assert AnalysisRequest(content="x", max_root_causes=1).max_root_causes == 1
        assert AnalysisRequest(content="x", max_root_causes=20).max_root_causes == 20


class TestValidationResult:
    def test_error_count_counts_high_and_critical_only(self):
        result = ValidationResult(
            technology=Technology.KUBERNETES,
            source_kind=SourceKind.KUBERNETES_MANIFEST,
            valid=False,
            issues=[
                ValidationIssue(severity=Severity.LOW, message="a"),
                ValidationIssue(severity=Severity.MEDIUM, message="b"),
                ValidationIssue(severity=Severity.HIGH, message="c"),
                ValidationIssue(severity=Severity.CRITICAL, message="d"),
            ],
        )
        assert result.error_count == 2

    def test_no_issues(self):
        result = ValidationResult(
            technology=Technology.TERRAFORM,
            source_kind=SourceKind.TERRAFORM,
            valid=True,
        )
        assert result.error_count == 0
        assert result.issues == []


class TestEnumStr:
    def test_str_is_value(self):
        assert str(Technology.KUBERNETES) == "kubernetes"
        assert str(SourceKind.LOG) == "log"
        assert str(Severity.HIGH) == "high"
