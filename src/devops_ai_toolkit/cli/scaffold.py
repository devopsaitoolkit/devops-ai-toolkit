"""Scaffolding for third-party plugins (``devops-ai create-plugin``).

Generates a complete, installable plugin project: package, plugin class, a sample
signature, packaging with the discovery entry point, a test, and a README. The
result installs with ``pip install -e .`` and is auto-discovered by the engine —
no core changes required.
"""

from __future__ import annotations

import re
from pathlib import Path

from .._version import __version__


def _normalise(name: str) -> tuple[str, str]:
    """Return ``(distribution_name, package_name)`` from a raw plugin name."""
    dist = re.sub(r"[^a-z0-9-]+", "-", name.strip().lower()).strip("-") or "my-plugin"
    package = dist.replace("-", "_")
    return dist, package


def create_plugin(name: str, destination: str | Path = ".") -> Path:
    """Generate a new plugin project under ``destination`` and return its path."""
    dist, package = _normalise(name)
    root = Path(destination) / dist
    pkg_dir = root / package
    tests_dir = root / "tests"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    tests_dir.mkdir(parents=True, exist_ok=True)

    files = _render(dist, package)
    for relative, content in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


def _render(dist: str, package: str) -> dict[str, str]:
    """Return a mapping of relative path -> file content for the new project."""
    title = package.replace("_", " ").title()
    return {
        f"{package}/__init__.py": f'"""The {dist} plugin for DevOps AI Toolkit."""\n\n'
        f'from .plugin import PLUGIN\n\n__all__ = ["PLUGIN"]\n',
        f"{package}/plugin.py": _PLUGIN_PY.format(package=package, dist=dist, title=title),
        "pyproject.toml": _PYPROJECT.format(dist=dist, package=package, core_version=__version__),
        "README.md": _README.format(dist=dist, package=package, title=title),
        "tests/test_plugin.py": _TEST_PY.format(package=package),
        ".gitignore": "__pycache__/\n*.egg-info/\n.venv/\ndist/\nbuild/\n",
    }


_PLUGIN_PY = '''"""The {title} analyzer plugin."""

from __future__ import annotations

from devops_ai_toolkit.models.enums import Technology
from devops_ai_toolkit.models.knowledge import (
    CauseTemplate,
    MatchSpec,
    Signature,
)
from devops_ai_toolkit.models.analysis import DiagnosticCommand, Reference
from devops_ai_toolkit.plugins import KnowledgeBackedPlugin, PluginMetadata

# Define your error signatures here. Each signature maps an error pattern to
# ranked root causes, READ-ONLY diagnostic commands, and references.
SIGNATURES = [
    Signature(
        id="{package}.example_error",
        technology=Technology.UNKNOWN,
        title="Example error this plugin detects",
        summary="Describe what this error means and when it occurs.",
        match=MatchSpec(any_of=["example error pattern"], weight=0.7),
        root_causes=[
            CauseTemplate(
                title="The most likely cause",
                description="Explain the cause and the evidence for it.",
                confidence=0.6,
                category="configuration",
            ),
        ],
        diagnostic_commands=[
            DiagnosticCommand(
                command="echo 'replace with a READ-ONLY diagnostic command'",
                explanation="What this command inspects and why it helps.",
                expected_output="What a healthy result looks like.",
            ),
        ],
        references=[
            Reference(title="Your docs", url="https://example.com", source="docs"),
        ],
        best_practices=["A best practice to prevent this error."],
        tags=["example"],
    ),
]

METADATA = PluginMetadata(
    name="{dist}",
    version="0.1.0",
    description="A custom DevOps AI Toolkit plugin.",
    author="Your Name",
    homepage="https://example.com",
    repository="https://github.com/you/{dist}",
    license="MIT",
    minimum_core_version="0.1.0",
    tags=["custom"],
    supported_technologies=[Technology.UNKNOWN],
    supported_file_types=[".log"],
)

# The engine discovers this object via the entry point declared in pyproject.toml.
PLUGIN = KnowledgeBackedPlugin(METADATA, SIGNATURES)
'''


_PYPROJECT = """[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{dist}"
version = "0.1.0"
description = "A DevOps AI Toolkit plugin"
requires-python = ">=3.12"
dependencies = ["devops-ai-toolkit>={core_version}"]

[project.optional-dependencies]
dev = ["pytest>=8.2"]

# This entry point is how the engine discovers the plugin once installed.
[project.entry-points."devops_ai_toolkit.plugins"]
{dist} = "{package}.plugin:PLUGIN"

[tool.hatch.build.targets.wheel]
packages = ["{package}"]
"""


_README = """# {title} — DevOps AI Toolkit Plugin

A plugin for [DevOps AI Toolkit](https://github.com/devopsaitoolkit/devops-ai-toolkit).

## Install (editable, for development)

```bash
pip install -e .
```

The engine discovers the plugin automatically via the
`devops_ai_toolkit.plugins` entry point. Verify with:

```bash
devops-ai plugins list
devops-ai plugins info {dist}
```

## Develop

1. Edit `{package}/plugin.py` — add `Signature` entries with your error patterns,
   root causes, and READ-ONLY diagnostic commands.
2. Update the `PluginMetadata` (name, technologies, file types, tags).
3. Run the tests: `pytest`.

## Publish

```bash
python -m build
twine upload dist/*
```

Users then `pip install {dist}` and the plugin is available immediately.
See the plugin guide: https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md
"""


_TEST_PY = '''"""Tests for the {package} plugin."""

from devops_ai_toolkit.plugins import AnalyzerPlugin

from {package} import PLUGIN


def test_plugin_is_valid() -> None:
    assert isinstance(PLUGIN, AnalyzerPlugin)
    meta = PLUGIN.metadata()
    assert meta.name
    assert meta.is_compatible()


def test_plugin_analyzes() -> None:
    result = PLUGIN.analyze("example error pattern in a log line")
    assert result.matched
'''
