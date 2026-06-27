# Plugin development

A step-by-step guide to building, testing, packaging and publishing a third-party
plugin. For the concepts behind the plugin system, read [Plugins](plugins.md)
first.

The whole flow is:

```bash
devops-ai create-plugin mycompany-plugin   # scaffold an installable project
cd mycompany-plugin
pip install -e .                             # auto-discovered immediately
devops-ai plugins list                       # confirm it appears
# edit signatures + metadata, run pytest, then publish to PyPI
```

No core changes are ever required: the engine discovers your plugin through the
`devops_ai_toolkit.plugins` entry point declared in the generated `pyproject.toml`.

---

## 1. Scaffold the project

```bash
devops-ai create-plugin mycompany-plugin
# Created plugin project at mycompany-plugin
#
# Next steps:
#   cd mycompany-plugin
#   pip install -e .
#   devops-ai plugins list   # your plugin appears, auto-discovered
```

The name is normalised to a valid distribution/package name (lowercased, with
non-alphanumeric runs collapsed to `-`). Use `--dir/-d` to choose where the
project is created:

```bash
devops-ai create-plugin mycompany-plugin --dir ~/src
```

### Generated layout

```
mycompany-plugin/
├── mycompany_plugin/
│   ├── __init__.py          # exposes PLUGIN
│   └── plugin.py            # SIGNATURES + METADATA + PLUGIN
├── tests/
│   └── test_plugin.py       # validity + analysis tests
├── pyproject.toml           # hatchling build + the discovery entry point
├── README.md
└── .gitignore
```

`__init__.py` re-exports `PLUGIN`, and `pyproject.toml` wires the entry point so
the engine finds it:

```toml
[project.entry-points."devops_ai_toolkit.plugins"]
mycompany-plugin = "mycompany_plugin.plugin:PLUGIN"
```

---

## 2. Edit signatures and metadata

Open `mycompany_plugin/plugin.py`. The two things you edit are the **signatures**
(what the plugin detects) and the **metadata** (how it describes itself).

### Signatures

Each `Signature` maps an error pattern to ranked root causes, **read-only**
diagnostic commands, and references:

```python
from devops_ai_toolkit.models.enums import Technology
from devops_ai_toolkit.models.knowledge import CauseTemplate, MatchSpec, Signature
from devops_ai_toolkit.models.analysis import DiagnosticCommand, Reference

SIGNATURES = [
    Signature(
        id="mycompany_plugin.tls_handshake_failure",
        technology=Technology.UNKNOWN,
        title="TLS handshake failed",
        summary="The client and server could not agree on a TLS session.",
        match=MatchSpec(any_of=["tls handshake error", "SSL_ERROR_SYSCALL"], weight=0.8),
        root_causes=[
            CauseTemplate(
                title="Expired or mismatched certificate",
                description="The presented certificate is expired or for a different host.",
                confidence=0.7,
                category="security",
            ),
        ],
        diagnostic_commands=[
            DiagnosticCommand(
                command="openssl s_client -connect host:443 -servername host </dev/null",
                explanation="Inspect the certificate the server presents.",
                expected_output="A valid chain with a notAfter date in the future.",
            ),
        ],
        references=[Reference(title="Runbook", url="https://example.com", source="docs")],
        best_practices=["Automate certificate renewal and alert before expiry."],
        tags=["tls", "security"],
    ),
]
```

Keep diagnostic commands **read-only** — the toolkit's contract is that it never
mutates infrastructure. See [knowledge base](knowledge-base.md) for the full
`Signature` model.

### Metadata

```python
from devops_ai_toolkit.plugins import KnowledgeBackedPlugin, PluginMetadata

METADATA = PluginMetadata(
    name="mycompany-plugin",
    version="0.1.0",
    description="MyCompany's internal service error analyzer.",
    author="MyCompany SRE",
    homepage="https://mycompany.example",
    repository="https://github.com/mycompany/devops-ai-plugin",
    documentation="https://mycompany.example/docs/plugin",
    license="Apache-2.0",
    minimum_core_version="0.1.0",
    tags=["mycompany", "internal"],
    supported_technologies=[Technology.UNKNOWN],
    supported_file_types=[".log"],
    supported_commands=["journalctl -u myservice"],
)

PLUGIN = KnowledgeBackedPlugin(METADATA, SIGNATURES)
```

`supported_technologies`, `supported_file_types` and `supported_commands` drive
routing — they tell the engine which inputs your plugin can handle.

---

## 3. Test with pytest

The scaffold ships a working test that asserts the plugin is valid and analyzes a
sample. Install the dev extra and run it:

```bash
pip install -e ".[dev]"
pytest
```

```python
# tests/test_plugin.py
from devops_ai_toolkit.plugins import AnalyzerPlugin
from mycompany_plugin import PLUGIN

def test_plugin_is_valid() -> None:
    assert isinstance(PLUGIN, AnalyzerPlugin)
    meta = PLUGIN.metadata()
    assert meta.name
    assert meta.is_compatible()

def test_plugin_analyzes() -> None:
    result = PLUGIN.analyze("tls handshake error while connecting")
    assert result.matched
```

Add a test per signature: feed a representative log line to `PLUGIN.analyze(...)`
and assert the expected root cause appears. You can also assert
`PLUGIN.supports(content, filename="x.log")` and `PLUGIN.explain("...")`.

Verify discovery end-to-end after installing:

```bash
devops-ai plugins list                 # mycompany-plugin shows source=entrypoint
devops-ai plugins info mycompany-plugin
devops-ai plugins doctor               # no failures
```

---

## 4. Packaging

The generated `pyproject.toml` uses **hatchling** and declares the discovery entry
point. Nothing else is required for the engine to find your plugin.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "mycompany-plugin"
version = "0.1.0"
description = "A DevOps AI Toolkit plugin"
requires-python = ">=3.12"
dependencies = ["devops-ai-toolkit>=0.1.0"]

[project.optional-dependencies]
dev = ["pytest>=8.2"]

[project.entry-points."devops_ai_toolkit.plugins"]
mycompany-plugin = "mycompany_plugin.plugin:PLUGIN"

[tool.hatch.build.targets.wheel]
packages = ["mycompany_plugin"]
```

Build the distributions:

```bash
pip install build
python -m build        # produces dist/*.whl and dist/*.tar.gz
```

---

## 5. Publishing to PyPI

```bash
pip install twine
twine upload dist/*
```

Once published, users get your plugin with one command and it is discovered
automatically:

```bash
pip install mycompany-plugin
devops-ai plugins list      # mycompany-plugin is now available
```

For a private/internal index (no public PyPI) and signed distribution, see
[enterprise plugins](enterprise-plugins.md). To make your plugin discoverable in
the planned online registry, fill in the marketplace metadata fields — see
[plugin marketplace](plugin-marketplace.md).

---

## 6. Versioning and compatibility

Use **semantic versioning** for your plugin's own `version`, and pin the lowest
core version you support with `minimum_core_version`:

- Bump **patch** for fixes to signatures/wording.
- Bump **minor** for new signatures or capabilities (backwards compatible).
- Bump **major** for breaking changes to the plugin's behaviour or metadata.

At load time the manager calls `metadata.is_compatible(core_version)`, comparing
`minimum_core_version` against the installed core. If the core is too old, the
plugin is recorded as a **failure** (visible in `plugins doctor`) and skipped — it
never crashes the engine:

```
requires core >= 2.0.0, have 0.1.0
```

Set `minimum_core_version` to the oldest core release whose API surface your
plugin relies on. Raise it only when you start using a newer feature.

---

## 7. Dependency management

- Always depend on `devops-ai-toolkit` with a floor that matches your
  `minimum_core_version` (the scaffold does this for you:
  `dependencies = ["devops-ai-toolkit>=0.1.0"]`).
- Add any runtime libraries your signatures or validator need under
  `[project.dependencies]`; keep test-only tools under the `dev` extra.
- Prefer wide, well-justified version ranges so your plugin co-installs cleanly
  with the core and with other plugins.
- A plugin that fails to import because of a missing/incompatible dependency is
  isolated as a load failure — `devops-ai plugins doctor` will tell you exactly
  why, so dependency problems are diagnosable, not fatal.

---

## See also

- [Plugins](plugins.md) — the interface, discovery, lifecycle and CLI/REST.
- [Plugin marketplace](plugin-marketplace.md) — metadata schema for publishing.
- [Enterprise plugins](enterprise-plugins.md) — private, signed, offline plugins.
- [Knowledge base](knowledge-base.md) — the `Signature` model in depth.
- More guides at <https://devopsaitoolkit.com>.
