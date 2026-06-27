# Plugins

The DevOps AI Toolkit is built as a **plugin architecture**. Every technology the
toolkit understands — Kubernetes, Terraform, PostgreSQL, NGINX, and 20+ more — is
an *independent plugin*. The core engine contains **no technology-specific logic**:
it discovers plugins, checks their compatibility, and routes each input to a
plugin that can handle it. Installing a new plugin requires **no core changes**.

This guide covers what plugins are, the `AnalyzerPlugin` interface, how discovery
and the lifecycle work, configuration, and how to write your own plugin. For the
hands-on workflow see [plugin development](plugin-development.md); for distribution
see the [plugin marketplace](plugin-marketplace.md) and
[enterprise plugins](enterprise-plugins.md) guides. The LLM/AI layer is *also* a
plugin point — see [LLM providers](llm-providers.md).

---

## What a plugin is

A plugin is a Python object implementing the `AnalyzerPlugin` interface plus a
self-describing `PluginMetadata`. It owns:

- **Metadata** — name, version, author, license, compatibility, capabilities.
- **Knowledge** — the error *signatures* (patterns → ranked root causes →
  read-only diagnostic commands → references) for one technology.
- **Behaviour** — how to decide whether it can handle an input (`supports`),
  how to analyze it (`analyze`), and how to validate/explain/extract.

Because the core only depends on the *interface*, a plugin is fully self-contained:
ship it as an installable Python package and the engine picks it up automatically.

> The toolkit is **read-only**. Plugins inspect text and produce guidance; the
> diagnostic commands they suggest are read-only by convention. A plugin never
> executes commands or mutates infrastructure.

---

## The `AnalyzerPlugin` interface

Defined in `devops_ai_toolkit.plugins.base`. The four abstract `extract_*`
methods, plus `metadata`, `supports`, `analyze`, `validate` and `explain`, are
required; `signatures` is optional (defaults to an empty list).

| Method | Required | Returns | Purpose |
| --- | --- | --- | --- |
| `metadata()` | yes | `PluginMetadata` | Self-describing metadata (name, version, capabilities, …). |
| `name` (property) | — | `str` | Shortcut for `metadata().name`. |
| `version` (property) | — | `str` | Shortcut for `metadata().version`. |
| `supports(content, *, technology=None, source_kind=None, filename=None)` | yes | `bool` | True if this plugin can analyze the given input. |
| `analyze(content, *, technology=None, source_kind=None, filename=None, max_root_causes=5)` | yes | `AnalysisResult` | Analyze `content` and return ranked findings. |
| `validate(content, *, filename=None)` | yes | `ValidationResult` | Validate a manifest/config (read-only). |
| `explain(query)` | yes | `ExplainResult \| None` | Explain a named error this plugin knows, or `None`. |
| `extract_errors(content)` | yes | `list[str]` | Error lines/messages found in `content`. |
| `extract_warnings(content)` | yes | `list[str]` | Warning lines/messages found in `content`. |
| `extract_resources(content)` | yes | `list[str]` | Resource identifiers referenced in `content`. |
| `extract_recommendations(result)` | yes | `list[str]` | Actionable recommendations from a result. |
| `signatures()` | no | `list[Signature]` | Knowledge-base signatures contributed (default: `[]`). |

You rarely implement these by hand. Subclass **`KnowledgeBackedPlugin`** instead
(see [below](#writing-a-plugin)) — it implements the entire interface from a list
of `Signature` objects plus optional validator, which is how all 20+ built-ins are
built.

---

## Discovery and registration

The `PluginManager` (`devops_ai_toolkit.plugins.manager`) discovers plugins from
**two independent sources**, which is exactly why the engine needs no code changes
when a plugin is installed:

1. **Built-in plugins.** Every module under
   `devops_ai_toolkit.plugins.builtin` that exposes a module-level `PLUGIN`
   (an `AnalyzerPlugin` instance) is discovered by module iteration.

2. **Third-party plugins.** Any installed distribution that advertises a
   **`devops_ai_toolkit.plugins`** entry point is loaded. The entry point may
   resolve to an `AnalyzerPlugin` instance or to a zero-arg callable that returns
   one.

```toml
# In a third-party plugin's pyproject.toml — this is all discovery needs:
[project.entry-points."devops_ai_toolkit.plugins"]
my-plugin = "my_plugin.plugin:PLUGIN"
```

Each load is **isolated**. A plugin that raises on import, fails to construct, or
is incompatible is recorded as a *failure* and surfaced by `plugins doctor` — it
never crashes the manager or the engine.

```python
from devops_ai_toolkit.plugins import PluginManager

manager = PluginManager.create_default()   # discovers built-ins + entry points
print(len(manager.all_plugins()))           # 21 built-ins, plus any installed
```

### Conflict resolution

If two plugins declare the same `name`, an **entry-point plugin overrides a
built-in** (logged as a warning) — this is how an organisation ships an improved
replacement for a built-in. Any other duplicate is rejected and recorded as a
failure, so the first one wins and the engine stays deterministic.

---

## The plugin lifecycle

```
 discover ──► compatibility check ──► load ──► enable / disable ──► route
 (builtin +    (minimum_core_version    (register   (persisted state)   (supports() picks
  entrypoints)  vs installed core)        instance)                      the plugin)
```

1. **Discover.** `manager.discover()` walks the built-in package and the entry
   points (idempotent).
2. **Compatibility check.** Before registering, the manager calls
   `metadata.is_compatible(core_version)`, comparing the plugin's
   `minimum_core_version` against the installed core version. Incompatible plugins
   become failures, not crashes.
3. **Load / register.** Compatible plugins are stored as `LoadedPlugin`
   (`plugin`, `source`, `enabled=True`).
4. **Enable / disable.** `manager.enable(name)` / `manager.disable(name)` flip a
   plugin on or off. The CLI persists this choice (see below) so disabled plugins
   are skipped during analysis, not merely hidden.
5. **Route.** `manager.plugin_for(content, …)` returns the first *enabled* plugin
   whose `supports()` returns True; `plugin_for_technology()` routes by an explicit
   `Technology`. Enabled plugins' signatures are aggregated into one knowledge base
   (`aggregate_knowledge_base()`).

### Health: `doctor()`

`manager.doctor()` returns a report you can act on:

```json
{
  "core_version": "0.1.0",
  "loaded": 21,
  "enabled": 21,
  "signatures": 480,
  "failures": [
    {"name": "broken-plugin", "source": "entrypoint", "reason": "requires core >= 2.0.0, have 0.1.0"}
  ]
}
```

---

## Configuration

### Enable / disable state

Enable/disable is **persisted** so the choice survives across invocations and is
read by the analysis commands too. The CLI writes a small JSON state file:

- `$DEVOPS_AI_STATE` if set — an explicit path to the state file.
- otherwise `$XDG_CONFIG_HOME/devops-ai/plugins.json`
  (defaults to `~/.config/devops-ai/plugins.json`).

```json
{ "disabled": ["vmware", "openstack"] }
```

```bash
export DEVOPS_AI_STATE=/etc/devops-ai/plugins.json   # team-wide state file
devops-ai plugins disable vmware                      # writes to that file
```

---

## Writing a plugin

The fast path is to subclass `KnowledgeBackedPlugin`
(`devops_ai_toolkit.plugins.knowledge_backed`): supply metadata, a list of
`Signature` rules, and an optional validator — the base class implements the whole
`AnalyzerPlugin` interface (matching, extraction, explanation) for you.

```python
"""my_plugin/plugin.py — a complete, installable plugin."""

from __future__ import annotations

from devops_ai_toolkit.models.enums import Technology
from devops_ai_toolkit.models.knowledge import CauseTemplate, MatchSpec, Signature
from devops_ai_toolkit.models.analysis import DiagnosticCommand, Reference
from devops_ai_toolkit.plugins import KnowledgeBackedPlugin, PluginMetadata

SIGNATURES = [
    Signature(
        id="my_plugin.connection_refused",
        technology=Technology.UNKNOWN,
        title="Connection refused to upstream service",
        summary="The client could not reach the service; the port is closed or the service is down.",
        match=MatchSpec(any_of=["connection refused", "ECONNREFUSED"], weight=0.8),
        root_causes=[
            CauseTemplate(
                title="The service is not listening on the expected port",
                description="The process crashed or never bound the port.",
                confidence=0.7,
                category="availability",
            ),
        ],
        diagnostic_commands=[
            DiagnosticCommand(
                command="ss -ltnp | grep ':8080'",          # READ-ONLY
                explanation="Show whether anything is listening on the port.",
                expected_output="A LISTEN row owned by the service process.",
            ),
        ],
        references=[
            Reference(title="Runbook", url="https://example.com/runbook", source="docs"),
        ],
        best_practices=["Add a readiness probe so traffic only routes to a bound port."],
        tags=["networking"],
    ),
]

METADATA = PluginMetadata(
    name="my-plugin",
    version="0.1.0",
    description="Analyzes upstream connectivity failures.",
    author="Your Name",
    homepage="https://example.com",
    repository="https://github.com/you/my-plugin",
    license="MIT",
    minimum_core_version="0.1.0",
    tags=["networking"],
    supported_technologies=[Technology.UNKNOWN],
    supported_file_types=[".log"],
)

# The engine discovers this object via the pyproject entry point.
PLUGIN = KnowledgeBackedPlugin(METADATA, SIGNATURES)
```

`supports()` returns True when the input matches the plugin's declared
`supported_technologies`, one of its `supported_file_types`, or any of its
signatures. `analyze()` matches the signatures and assembles a ranked
`AnalysisResult` labelled `plugin:<name>`. If you pass a `validator` callable, it
is applied to YAML/Kubernetes/Terraform/Compose inputs and merged into the result.

You don't have to write the boilerplate yourself — `devops-ai create-plugin`
scaffolds exactly this project. See [plugin development](plugin-development.md).

---

## Built-in plugins

The toolkit ships 20+ built-in plugins, each an independent `AnalyzerPlugin`
covering one technology family. They partition the packaged knowledge base by
`Technology`, so the YAML signature data is the single source of truth and is never
duplicated.

| Plugin | Covers |
| --- | --- |
| `kubernetes` | Kubernetes & OpenShift pods, scheduling, manifests |
| `docker` | Docker engine and container runtime errors |
| `docker_compose` | Compose file and multi-container errors |
| `terraform` | Terraform plan/apply and HCL errors |
| `ansible` | Ansible playbook and task failures |
| `systemd` | systemd units and the journal |
| `linux` | Generic Linux/kernel/syslog issues |
| `nginx` | NGINX config and access/error logs |
| `postgresql` | PostgreSQL server and query errors |
| `mysql` | MySQL/MariaDB errors |
| `redis` | Redis server and client errors |
| `rabbitmq` | RabbitMQ broker errors |
| `prometheus` | Prometheus scrape/rule errors |
| `grafana` | Grafana datasource and dashboard errors |
| `gitlab_ci` | GitLab CI pipeline failures |
| `aws` | AWS service and SDK errors |
| `azure` | Azure service errors |
| `gcp` | Google Cloud errors |
| `openstack` | OpenStack (Nova, Neutron, …) errors |
| `vmware` | VMware/vSphere errors |
| `ceph` | Ceph storage errors |
| `linstor` | LINSTOR/DRBD storage errors |

List the live set on your machine with `devops-ai plugins list`. See also
[supported technologies](supported-technologies.md).

---

## CLI commands

`devops-ai plugins` is the management surface (`devops_ai_toolkit.cli.plugins`):

```bash
devops-ai plugins list               # all discovered plugins + status
devops-ai plugins info kubernetes    # full metadata (JSON) for one plugin
devops-ai plugins enable vmware      # enable (persisted)
devops-ai plugins disable vmware     # disable (persisted)
devops-ai plugins doctor             # health check; non-zero exit if failures
devops-ai plugins update             # how to update installed plugin packages
```

`plugins list` shows name, version, source (`builtin`/`entrypoint`), status, and
technologies, and warns if any plugin failed to load. To scaffold a brand-new
plugin:

```bash
devops-ai create-plugin mycompany-plugin
```

---

## REST endpoints

The API mirrors the CLI (`devops_ai_toolkit.api.plugins`):

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/plugins` | List all plugins (name, version, source, enabled, technologies). |
| `GET` | `/plugins/{name}` | Full `PluginMetadata` for one plugin (404 if unknown). |
| `POST` | `/plugins/enable` | Enable a plugin for this server process (`{"name": "..."}`). |
| `POST` | `/plugins/disable` | Disable a plugin for this server process (`{"name": "..."}`). |

```bash
curl localhost:8000/plugins
curl localhost:8000/plugins/kubernetes
curl -X POST localhost:8000/plugins/disable -d '{"name":"vmware"}' -H 'content-type: application/json'
```

---

## See also

- [Plugin development](plugin-development.md) — scaffold, test, package, publish.
- [Plugin marketplace](plugin-marketplace.md) — the metadata schema and the registry vision.
- [Enterprise plugins](enterprise-plugins.md) — private, signed, offline, pinned plugins.
- [LLM providers](llm-providers.md) — the AI layer is a plugin point too.
- [Knowledge base](knowledge-base.md) — how signatures work.
- More tutorials at <https://devopsaitoolkit.com>.
