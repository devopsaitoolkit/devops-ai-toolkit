"""Packaged knowledge-base data.

Each ``*.yaml`` file in this directory contains a list of error *signatures* (see
:class:`devops_ai_toolkit.models.knowledge.Signature`). Add a YAML file here to
extend coverage — no engine code changes are needed. Files are validated at load
time, so a malformed signature fails fast and loudly.
"""
