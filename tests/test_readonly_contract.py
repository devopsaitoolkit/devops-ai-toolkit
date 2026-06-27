"""Enforce the toolkit's read-only guarantee programmatically.

The product promise is that every suggested diagnostic command is non-mutating.
This test scans every diagnostic command in the whole knowledge base for verbs
that would change infrastructure or data, and fails if any are present.
"""

from __future__ import annotations

import re

import pytest

from devops_ai_toolkit.knowledge.loader import load_default_knowledge_base

# Verbs / tokens that imply mutation. Matched case-insensitively as whole words.
_MUTATING_TOKENS = [
    "delete",
    "rm",
    "rmdir",
    "apply",
    "restart",
    "reboot",
    "shutdown",
    "scale",
    "drop",
    "truncate",
    "terminate",
    "destroy",
    "mkfs",
    "kill",
    "stop",
    "start",
    "create",
    "remove",
    "edit",
    "patch",
    "replace",
    "set",
    "unset",
    "cordon",
    "drain",
    "evict",
    "taint",
    "rollout",
    "purge",
    "flush",
    "format",
    "write",
    "modify",
    "update",
    "install",
    "uninstall",
    "chmod",
    "chown",
    "mv",
    "reset",
    "revert",
    "rollback",
]

# Read-only commands that legitimately contain a substring of a mutating word,
# or read-only subcommands of otherwise-mutating tools. These are allow-listed
# so the guard stays precise.
_ALLOWED_PHRASES = [
    "terraform state list",
    "terraform show",
    "terraform plan",
    "terraform validate",
    "terraform fmt -check",
    "systemctl status",
    "systemctl list",
    "systemctl is-",
    "systemctl show",
    "journalctl",
    "kubectl get",
    "kubectl describe",
    "kubectl logs",
    "kubectl top",
    "kubectl explain",
    "kubectl api-resources",
    "kubectl version",
    "kubectl config view",
    "kubectl auth can-i",
    "docker ps",
    "docker logs",
    "docker inspect",
    "docker stats",
]

_TOKEN_RE = {
    tok: re.compile(rf"(?<![\w-]){re.escape(tok)}(?![\w-])", re.IGNORECASE)
    for tok in _MUTATING_TOKENS
}


def _all_diagnostic_commands():
    kb = load_default_knowledge_base()
    for sig in kb.signatures:
        for cmd in sig.diagnostic_commands:
            yield sig.id, cmd


@pytest.mark.integration
class TestReadOnlyContract:
    def test_no_diagnostic_command_is_mutating(self):
        offenders: list[str] = []
        for sig_id, cmd in _all_diagnostic_commands():
            command = cmd.command
            lowered = command.lower()
            # `--help` / `--dry-run` invocations are inherently non-mutating.
            if "--help" in lowered or "--dry-run" in lowered:
                continue
            if any(phrase in lowered for phrase in _ALLOWED_PHRASES):
                continue
            for token, pattern in _TOKEN_RE.items():
                if pattern.search(command):
                    offenders.append(f"{sig_id}: {command!r} contains mutating verb {token!r}")
        assert not offenders, "Mutating diagnostic commands found:\n" + "\n".join(offenders)

    def test_diagnostic_commands_flagged_read_only(self):
        for sig_id, cmd in _all_diagnostic_commands():
            assert cmd.read_only is True, f"{sig_id}: command not marked read_only: {cmd.command!r}"

    def test_there_are_diagnostic_commands_to_check(self):
        # Guard against the scan passing vacuously.
        assert any(True for _ in _all_diagnostic_commands())
