"""Tests for the validators: YAML, Kubernetes, and Terraform."""

from __future__ import annotations

from devops_ai_toolkit.models.enums import Severity, SourceKind, Technology
from devops_ai_toolkit.validators.kubernetes import validate_kubernetes
from devops_ai_toolkit.validators.service import validate_manifest
from devops_ai_toolkit.validators.terraform import validate_terraform
from devops_ai_toolkit.validators.yaml_validator import validate_yaml


class TestYamlValidator:
    def test_valid_yaml(self):
        result = validate_yaml("foo: bar\nbaz: 1\n")
        assert result.valid is True
        assert result.issues == []

    def test_syntax_error_detected_with_line(self, invalid_yaml):
        result = validate_yaml(invalid_yaml)
        assert result.valid is False
        assert result.issues
        issue = result.issues[0]
        assert issue.severity is Severity.HIGH
        # parse error should carry a 1-based line number.
        assert issue.line is None or issue.line >= 1

    def test_unbalanced_bracket(self):
        result = validate_yaml("foo: [1, 2, 3\n")
        assert result.valid is False
        assert result.issues[0].line is not None
        assert result.issues[0].line >= 1


class TestKubernetesValidator:
    def test_valid_manifest(self, valid_k8s_manifest):
        result = validate_kubernetes(valid_k8s_manifest)
        assert result.technology is Technology.KUBERNETES
        assert result.source_kind is SourceKind.KUBERNETES_MANIFEST
        assert result.valid is True

    def test_missing_required_fields(self, bad_k8s_manifest):
        result = validate_kubernetes(bad_k8s_manifest)
        # 'metadata' is missing -> HIGH severity -> invalid.
        assert result.valid is False
        assert any("Missing required field" in i.message for i in result.issues)
        assert any(i.path.endswith(".metadata") for i in result.issues)

    def test_latest_tag_flagged(self, bad_k8s_manifest):
        result = validate_kubernetes(bad_k8s_manifest)
        assert any("mutable image tag" in i.message for i in result.issues)

    def test_no_resources_flagged(self, bad_k8s_manifest):
        result = validate_kubernetes(bad_k8s_manifest)
        assert any("resource requests/limits" in i.message for i in result.issues)

    def test_no_probes_flagged(self, bad_k8s_manifest):
        result = validate_kubernetes(bad_k8s_manifest)
        assert any("health probes" in i.message for i in result.issues)

    def test_best_practices_present(self, valid_k8s_manifest):
        result = validate_kubernetes(valid_k8s_manifest)
        assert result.best_practices

    def test_invalid_yaml_short_circuits(self):
        result = validate_kubernetes("a: b: c:\n  - : bad\n")
        assert result.valid is False
        assert result.issues[0].severity is Severity.HIGH


class TestTerraformValidator:
    def test_valid_terraform(self, valid_terraform):
        result = validate_terraform(valid_terraform)
        assert result.technology is Technology.TERRAFORM
        assert result.valid is True
        assert result.issues == []

    def test_unbalanced_braces(self, unbalanced_terraform):
        result = validate_terraform(unbalanced_terraform)
        assert result.valid is False
        assert any("Unbalanced braces" in i.message for i in result.issues)

    def test_unbalanced_quotes(self):
        result = validate_terraform('resource "aws_s3_bucket" "x" {\n  bucket = "unterminated\n}\n')
        assert result.valid is False
        assert any("Unbalanced double quotes" in i.message for i in result.issues)

    def test_no_blocks_is_low_severity(self):
        result = validate_terraform("region = us-east-1\n")
        # Only a LOW issue -> still 'valid' (no HIGH/CRITICAL).
        assert result.valid is True
        assert any(i.severity is Severity.LOW for i in result.issues)

    def test_braces_in_strings_not_miscounted(self):
        # Braces inside string literals must not unbalance the count.
        text = 'resource "aws_iam_policy" "p" {\n  policy = "{ not a real brace"\n}\n'
        result = validate_terraform(text)
        assert result.valid is True


class TestValidateService:
    def test_dispatches_terraform_by_source_kind(self, valid_terraform):
        result = validate_manifest(valid_terraform, source_kind=SourceKind.TERRAFORM)
        assert result.technology is Technology.TERRAFORM

    def test_dispatches_kubernetes(self, valid_k8s_manifest):
        result = validate_manifest(valid_k8s_manifest)
        assert result.technology is Technology.KUBERNETES

    def test_dispatches_plain_yaml_fallback(self):
        result = validate_manifest("just: some\nplain: yaml\n")
        assert result.technology is Technology.UNKNOWN
        assert result.source_kind is SourceKind.YAML
