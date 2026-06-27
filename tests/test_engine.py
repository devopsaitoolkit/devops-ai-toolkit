"""Tests for the AnalysisEngine — the single façade over the pipeline."""

from __future__ import annotations

from devops_ai_toolkit.analysis import AnalysisEngine
from devops_ai_toolkit.models.analysis import AnalysisRequest
from devops_ai_toolkit.models.enums import Severity, SourceKind, Technology


class TestAnalyzeText:
    def test_crashloop(self, engine, crashloop_log):
        result = engine.analyze_text(crashloop_log)
        assert result.matched is True
        assert "k8s.crashloopbackoff" in result.signatures_matched
        assert result.technology is Technology.KUBERNETES
        assert result.confidence > 0.0
        assert result.root_causes

    def test_benign_no_match(self, engine, benign_text):
        result = engine.analyze_text(benign_text)
        assert result.matched is False
        assert result.root_causes == []
        assert "did not match" in result.summary

    def test_summary_mentions_top_cause(self, engine, crashloop_log):
        result = engine.analyze_text(crashloop_log)
        assert "confidence" in result.summary.lower()

    def test_metadata_present(self, engine, crashloop_log):
        result = engine.analyze_text(crashloop_log)
        assert result.metadata["engine"] == "deterministic"
        assert int(result.metadata["signatures_evaluated"]) == len(engine.knowledge_base)


class TestAnalyzeFile:
    def test_reads_and_analyzes(self, engine, tmp_path, crashloop_log):
        p = tmp_path / "nova.log"
        p.write_text(crashloop_log, encoding="utf-8")
        result = engine.analyze_file(p)
        assert "k8s.crashloopbackoff" in result.signatures_matched

    def test_accepts_str_path(self, engine, tmp_path):
        # A pod-flavoured OOMKilled line so technology detection lands on k8s.
        text = "pod/app-1 container terminated: OOMKilled exit code 137\n"
        p = tmp_path / "out.log"
        p.write_text(text, encoding="utf-8")
        result = engine.analyze_file(str(p))
        assert "k8s.oomkilled" in result.signatures_matched


class TestAnalyzeYamlTerraform:
    def test_analyze_yaml_sets_source_kind(self, engine, valid_k8s_manifest):
        result = engine.analyze_yaml(valid_k8s_manifest)
        assert result.source_kind is SourceKind.YAML

    def test_analyze_terraform_hints(self, engine, terraform_state_lock_log):
        result = engine.analyze_terraform(terraform_state_lock_log)
        assert result.technology is Technology.TERRAFORM
        assert result.source_kind is SourceKind.TERRAFORM
        assert "terraform.state_lock" in result.signatures_matched


class TestTechnologyAutoDetection:
    def test_detects_kubernetes(self, engine, crashloop_log):
        assert engine.analyze_text(crashloop_log).technology is Technology.KUBERNETES

    def test_explicit_hint_overrides(self, engine, benign_text):
        result = engine.analyze_text(benign_text, technology=Technology.REDIS)
        assert result.technology is Technology.REDIS


class TestMaxRootCauses:
    def test_caps_root_causes(self, engine, crashloop_log):
        req = AnalysisRequest(content=crashloop_log, max_root_causes=1)
        result = engine.analyze(req)
        assert len(result.root_causes) <= 1

    def test_root_causes_sorted_by_confidence(self, engine, crashloop_log):
        result = engine.analyze_text(crashloop_log)
        confidences = [rc.confidence for rc in result.root_causes]
        assert confidences == sorted(confidences, reverse=True)


class TestExplainError:
    def test_explain_known(self, engine):
        result = engine.explain_error("CrashLoopBackOff")
        assert result.matched is True
        assert result.technology is Technology.KUBERNETES
        assert result.root_causes
        assert result.diagnostic_commands

    def test_explain_by_id(self, engine):
        result = engine.explain_error("k8s.oomkilled")
        assert result.matched is True
        assert "OOMKilled" in result.title

    def test_explain_unknown(self, engine):
        result = engine.explain_error("zzz totally unknown nonsense error zzz")
        assert result.matched is False
        assert result.title == "zzz totally unknown nonsense error zzz"
        assert result.root_causes == []


class TestValidateManifest:
    def test_terraform_unbalanced(self, engine, unbalanced_terraform):
        result = engine.validate_manifest(unbalanced_terraform)
        assert result.technology is Technology.TERRAFORM
        assert result.valid is False

    def test_kubernetes_missing_fields(self, engine, bad_k8s_manifest):
        result = engine.validate_manifest(bad_k8s_manifest)
        assert result.valid is False
        assert any("Missing required field" in i.message for i in result.issues)


class TestEnrichmentDegradesGracefully:
    def test_no_provider_adds_low_severity_warning(self, offline_settings, crashloop_log):
        engine = AnalysisEngine(settings=offline_settings)
        result = engine.analyze_text(crashloop_log, enrich=True)
        # No exception, deterministic results still present.
        assert result.matched is True
        assert result.enrichment is None
        warnings = [w for w in result.warnings if w.severity is Severity.LOW]
        assert any("no provider" in w.message.lower() for w in warnings)

    def test_provider_failure_does_not_break(
        self, offline_settings, failing_provider, crashloop_log
    ):
        engine = AnalysisEngine(provider=failing_provider, settings=offline_settings)
        result = engine.analyze_text(crashloop_log, enrich=True)
        # RuntimeError from provider is swallowed; result returned, no enrichment.
        assert result.matched is True
        assert result.enrichment is None

    def test_working_provider_enriches(self, offline_settings, fake_provider, crashloop_log):
        engine = AnalysisEngine(provider=fake_provider, settings=offline_settings)
        result = engine.analyze_text(crashloop_log, enrich=True)
        assert result.enrichment is not None
        assert result.enrichment.provider == "fake"
        assert result.enrichment.model == "fake-model-1"
        assert "fake narrative" in result.enrichment.narrative.lower()
        assert "Extra hypothesis one." in result.enrichment.additional_causes
        assert fake_provider.calls  # provider was actually invoked


class TestInjection:
    def test_engine_uses_injected_kb(self, knowledge_base, offline_settings):
        engine = AnalysisEngine(knowledge_base=knowledge_base, settings=offline_settings)
        assert engine.knowledge_base is knowledge_base
