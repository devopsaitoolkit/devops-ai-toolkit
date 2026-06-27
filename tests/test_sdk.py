"""Tests for the documented Python SDK flow and JSON round-tripping."""

from __future__ import annotations

import json

from devops_ai_toolkit import (
    AnalysisEngine,
    AnalysisRequest,
    AnalysisResult,
    ErrorCatalog,
    ExplainResult,
    SourceKind,
    Technology,
    ValidationResult,
    __version__,
)
from devops_ai_toolkit.output.serialize import to_json


class TestPublicSurface:
    def test_documented_imports(self):
        assert callable(AnalysisEngine)
        assert __version__
        assert issubclass(AnalysisResult, object)

    def test_quickstart_flow(self, tmp_path, crashloop_log):
        # Mirrors the README/quickstart: construct engine, analyze a file.
        p = tmp_path / "nova.log"
        p.write_text(crashloop_log, encoding="utf-8")
        engine = AnalysisEngine()
        result = engine.analyze_file(p)
        assert isinstance(result, AnalysisResult)
        assert result.summary
        assert result.matched is True


class TestJsonRoundTrip:
    def test_analysis_result_round_trips(self, engine, crashloop_log):
        result = engine.analyze_text(crashloop_log)
        payload = to_json(result)
        data = json.loads(payload)
        # Computed fields are included in serialization.
        assert "confidence" in data
        assert "confidence_percent" in data
        assert "matched" in data
        # Reconstruct and confirm equivalence of core fields.
        restored = AnalysisResult.model_validate(data)
        assert restored.technology is Technology.KUBERNETES
        assert restored.signatures_matched == result.signatures_matched
        assert restored.confidence == result.confidence

    def test_explain_result_round_trips(self, engine):
        result = engine.explain_error("CrashLoopBackOff")
        data = json.loads(to_json(result))
        restored = ExplainResult.model_validate(data)
        assert restored.matched is True
        assert restored.title == result.title

    def test_validation_result_round_trips(self, engine, bad_k8s_manifest):
        result = engine.validate_manifest(bad_k8s_manifest)
        data = json.loads(to_json(result))
        assert "error_count" in data
        restored = ValidationResult.model_validate(data)
        assert restored.valid == result.valid
        assert len(restored.issues) == len(result.issues)

    def test_request_model_round_trips(self):
        req = AnalysisRequest(content="x", technology=Technology.REDIS)
        data = json.loads(req.model_dump_json())
        restored = AnalysisRequest.model_validate(data)
        assert restored.technology is Technology.REDIS
        assert restored.source_kind is None


class TestErrorCatalog:
    def test_catalog_entries(self):
        catalog = ErrorCatalog()
        assert len(catalog) > 0
        entries = catalog.entries()
        assert any(e.id == "k8s.crashloopbackoff" for e in entries)
        # Sorted by id.
        ids = [e.id for e in entries]
        assert ids == sorted(ids)

    def test_catalog_filtered(self):
        entries = ErrorCatalog().entries(Technology.KUBERNETES)
        assert entries
        assert all(e.technology is Technology.KUBERNETES for e in entries)

    def test_catalog_grouped(self):
        grouped = ErrorCatalog().grouped()
        assert Technology.KUBERNETES in grouped
        assert all(isinstance(v, list) for v in grouped.values())

    def test_source_kind_enum_exported(self):
        assert SourceKind.LOG.value == "log"
