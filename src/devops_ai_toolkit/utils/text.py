"""Heuristics for detecting technology and input shape from raw text.

These are deliberately conservative: they provide a hint that the engine can use
when the caller does not specify ``technology`` / ``source_kind`` explicitly.
"""

from __future__ import annotations

import re

from ..models.enums import SourceKind, Technology

# Ordered (Technology, regex) pairs. First match wins, so put specific signals
# (e.g. 'nova-compute') before generic ones (e.g. 'error').
_TECH_SIGNALS: list[tuple[Technology, str]] = [
    (
        Technology.KUBERNETES,
        r"\b(crashloopbackoff|imagepullbackoff|kubelet|kube-apiserver|pod/|apiVersion:\s*(apps|v1))\b",
    ),
    (Technology.OPENSHIFT, r"\b(oc adm|openshift|securitycontextconstraints|scc)\b"),
    (
        Technology.TERRAFORM,
        r"(terraform\s+(apply|plan|init)|Error: .*provider|resource\s+\"[a-z_]+\"\s+\")",
    ),
    (Technology.ANSIBLE, r"(ansible-playbook|TASK \[|fatal:.*=>|gather_facts)"),
    (Technology.DOCKER_COMPOSE, r"(docker-compose|services:\s*$|compose\.ya?ml)"),
    (
        Technology.DOCKER,
        r"(docker:|OCI runtime|dockerd|/var/run/docker\.sock|Error response from daemon)",
    ),
    (
        Technology.OPENSTACK,
        r"\b(nova-compute|nova-conductor|cinder|neutron|keystone|glance|placement|No valid host)\b",
    ),
    (Technology.GITLAB_CI, r"(gitlab-runner|\.gitlab-ci\.yml|job failed: exit code|CI_JOB_TOKEN)"),
    (
        Technology.PROMETHEUS,
        r"(prometheus|promql|alertmanager|scrape_configs|out-of-order sample|tsdb)",
    ),
    (Technology.GRAFANA, r"\bgrafana\b"),
    (Technology.RABBITMQ, r"(rabbitmq|amqp|missed heartbeats|mnesia)"),
    (Technology.REDIS, r"\b(redis|MISCONF|maxmemory|RDB|AOF)\b"),
    (Technology.NGINX, r"(nginx|upstream|worker_connections|location\s+/)"),
    (Technology.APACHE, r"(apache|httpd|mod_|AH00[0-9]{3})"),
    (Technology.POSTGRESQL, r"(postgres|psql|FATAL:.*role|could not connect to server|pg_hba)"),
    (Technology.MYSQL, r"(mysql|mariadb|ER_|Access denied for user|Got error 28)"),
    (Technology.CEPH, r"\b(ceph|osd|HEALTH_(WARN|ERR)|placement group|rados)\b"),
    (Technology.LINSTOR, r"\b(linstor|drbd|satellite)\b"),
    (Technology.VMWARE, r"\b(vmware|esxi|vsphere|vcenter|vmkernel)\b"),
    (Technology.AWS, r"\b(aws|ec2|s3|iam|AccessDenied|us-east-1|arn:aws)\b"),
    (Technology.AZURE, r"\b(azure|az\s+cli|microsoft\.|AADSTS)\b"),
    (Technology.GCP, r"\b(gcloud|gke|google cloud|gcp|compute\.googleapis)\b"),
    (Technology.SYSTEMD, r"(systemd|systemctl|journalctl|\.service:|Failed to start)"),
    (Technology.LINUX, r"(kernel:|segfault|Out of memory|oom-killer|dmesg|/var/log)"),
]


def detect_technology(text: str, filename: str | None = None) -> Technology:
    """Best-effort detection of the technology a blob of text relates to."""
    haystack = text if not filename else f"{filename}\n{text}"
    for tech, pattern in _TECH_SIGNALS:
        if re.search(pattern, haystack, re.IGNORECASE | re.MULTILINE):
            return tech
    return Technology.UNKNOWN


def detect_source_kind(text: str, filename: str | None = None) -> SourceKind:
    """Best-effort detection of the input shape."""
    name = (filename or "").lower()
    if name.endswith(".tf") or re.search(r"^\s*resource\s+\"", text, re.MULTILINE):
        return SourceKind.TERRAFORM
    if "docker-compose" in name or re.search(r"^\s*services:\s*$", text, re.MULTILINE):
        return SourceKind.COMPOSE
    if re.search(r"^\s*apiVersion:\s*\S+", text, re.MULTILINE) and re.search(
        r"^\s*kind:\s*\S+", text, re.MULTILINE
    ):
        return SourceKind.KUBERNETES_MANIFEST
    if name.endswith((".yaml", ".yml")) or re.search(r"^\s*[\w.-]+:\s", text, re.MULTILINE):
        return SourceKind.YAML
    if name.endswith(".log") or re.search(r"\b(ERROR|WARN|FATAL|Traceback)\b", text):
        return SourceKind.LOG
    if "\n" not in text.strip():
        return SourceKind.ERROR_STRING
    return SourceKind.LOG


def truncate(text: str, limit: int) -> str:
    """Trim ``text`` to ``limit`` characters, keeping the most recent content.

    Logs are most informative at the tail (where failures surface), so we keep
    the end rather than the beginning when truncating.
    """
    if len(text) <= limit:
        return text
    return "...[truncated]...\n" + text[-limit:]
