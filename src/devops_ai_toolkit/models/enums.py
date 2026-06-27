"""Enumerations shared across the analysis domain.

These give every interface (CLI, SDK, REST API) a stable, typed vocabulary for
technologies, input kinds, severities and confidence bands.
"""

from __future__ import annotations

from enum import StrEnum


class Technology(StrEnum):
    """A supported technology / platform the engine can reason about."""

    DOCKER = "docker"
    DOCKER_COMPOSE = "docker_compose"
    KUBERNETES = "kubernetes"
    OPENSHIFT = "openshift"
    TERRAFORM = "terraform"
    ANSIBLE = "ansible"
    OPENSTACK = "openstack"
    LINUX = "linux"
    SYSTEMD = "systemd"
    GITLAB_CI = "gitlab_ci"
    PROMETHEUS = "prometheus"
    GRAFANA = "grafana"
    RABBITMQ = "rabbitmq"
    REDIS = "redis"
    NGINX = "nginx"
    APACHE = "apache"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    CEPH = "ceph"
    LINSTOR = "linstor"
    VMWARE = "vmware"
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    UNKNOWN = "unknown"


class SourceKind(StrEnum):
    """The shape of the input being analyzed."""

    LOG = "log"
    YAML = "yaml"
    TERRAFORM = "terraform"
    COMPOSE = "compose"
    KUBERNETES_MANIFEST = "kubernetes_manifest"
    COMMAND_OUTPUT = "command_output"
    ERROR_STRING = "error_string"
    UNKNOWN = "unknown"


class Severity(StrEnum):
    """Severity of a finding or warning."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceBand(StrEnum):
    """Human-friendly bucket for a numeric confidence score."""

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

    @classmethod
    def from_score(cls, score: float) -> ConfidenceBand:
        """Map a 0.0-1.0 confidence score to a band."""
        if score >= 0.85:
            return cls.VERY_HIGH
        if score >= 0.65:
            return cls.HIGH
        if score >= 0.45:
            return cls.MODERATE
        if score >= 0.25:
            return cls.LOW
        return cls.VERY_LOW
