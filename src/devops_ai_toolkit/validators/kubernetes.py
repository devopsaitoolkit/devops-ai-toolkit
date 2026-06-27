"""Structural best-practice checks for Kubernetes manifests (read-only)."""

from __future__ import annotations

from typing import Any

from ..models.analysis import ValidationIssue, ValidationResult
from ..models.enums import Severity, SourceKind, Technology
from ..parsers.yaml_docs import parse_yaml_documents

_REQUIRED_TOP_LEVEL = ("apiVersion", "kind", "metadata")
_WORKLOAD_KINDS = {"Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job", "CronJob"}


def validate_kubernetes(text: str) -> ValidationResult:
    """Validate Kubernetes manifests for required fields and common pitfalls.

    Checks performed (all read-only, advisory):
    - YAML parses cleanly
    - required top-level fields present (apiVersion, kind, metadata)
    - workloads declare resource requests/limits, probes, and image tags
    """
    parsed = parse_yaml_documents(text)
    issues: list[ValidationIssue] = []

    if not parsed.ok:
        issues.append(
            ValidationIssue(
                severity=Severity.HIGH,
                message=parsed.error or "Invalid YAML.",
                line=parsed.error_line,
            )
        )
        return _result(False, issues)

    for index, doc in enumerate(parsed.documents):
        if not isinstance(doc, dict):
            continue
        prefix = f"doc[{index}]"
        for key in _REQUIRED_TOP_LEVEL:
            if key not in doc:
                issues.append(
                    ValidationIssue(
                        severity=Severity.HIGH,
                        message=f"Missing required field '{key}'.",
                        path=f"{prefix}.{key}",
                        hint="Every Kubernetes object needs apiVersion, kind and metadata.",
                    )
                )
        if doc.get("kind") in _WORKLOAD_KINDS:
            issues.extend(_check_workload(doc, prefix))

    valid = not any(i.severity in (Severity.HIGH, Severity.CRITICAL) for i in issues)
    return _result(valid, issues)


def _check_workload(doc: dict[str, Any], prefix: str) -> list[ValidationIssue]:
    """Inspect a workload's pod template for reliability best practices."""
    issues: list[ValidationIssue] = []
    containers = doc.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [])
    if not isinstance(containers, list):
        return issues
    for container in containers:
        if not isinstance(container, dict):
            continue
        cname = container.get("name", "?")
        image = str(container.get("image", ""))
        if image.endswith(":latest") or (":" not in image and "@" not in image):
            issues.append(
                ValidationIssue(
                    severity=Severity.MEDIUM,
                    message=f"Container '{cname}' uses a mutable image tag.",
                    path=f"{prefix}.spec.template.spec.containers[{cname}].image",
                    hint="Pin to an immutable tag or digest for reproducible rollouts.",
                )
            )
        if not container.get("resources"):
            issues.append(
                ValidationIssue(
                    severity=Severity.MEDIUM,
                    message=f"Container '{cname}' has no resource requests/limits.",
                    path=f"{prefix}.spec.template.spec.containers[{cname}].resources",
                    hint="Set requests/limits to avoid noisy-neighbour and OOMKilled issues.",
                )
            )
        if not container.get("livenessProbe") and not container.get("readinessProbe"):
            issues.append(
                ValidationIssue(
                    severity=Severity.LOW,
                    message=f"Container '{cname}' defines no health probes.",
                    path=f"{prefix}.spec.template.spec.containers[{cname}]",
                    hint="Add readiness/liveness probes so Kubernetes can route and heal.",
                )
            )
    return issues


def _result(valid: bool, issues: list[ValidationIssue]) -> ValidationResult:
    return ValidationResult(
        technology=Technology.KUBERNETES,
        source_kind=SourceKind.KUBERNETES_MANIFEST,
        valid=valid,
        issues=issues,
        best_practices=[
            "Pin images to digests/immutable tags.",
            "Always set resource requests and limits.",
            "Define readiness and liveness probes.",
            "Run manifests through validation in CI.",
        ],
    )
