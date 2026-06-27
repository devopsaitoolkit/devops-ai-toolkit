# Plugin marketplace

The plugin architecture is designed so that plugins are **publishable and
discoverable** without any change to the core. Today plugins are installed as
ordinary Python packages (see [plugin development](plugin-development.md)); the
metadata schema below is deliberately a *superset* of what a future online
registry needs, so the same plugins you ship now will be indexable later with **no
schema migration**.

---

## The vision

A plugin is just an installable package that advertises a
`devops_ai_toolkit.plugins` entry point. That means a marketplace doesn't need any
special runtime support in the core — it only needs to:

1. **Index** published plugins by their `PluginMetadata` (name, tags, technologies,
   compatibility, author, links).
2. **Install** the matching distribution with the user's package manager
   (`pip install <plugin>`), which the engine then auto-discovers.
3. **Vet** plugins by inspecting their declared metadata — license, signing,
   minimum core version — before listing them.

Because discovery and compatibility are already part of the core
([Plugins → discovery](plugins.md#discovery-and-registration)), the registry is a
catalog-and-install layer on top, not a core change.

> Browse tutorials and announcements at <https://devopsaitoolkit.com>.

---

## The `PluginMetadata` schema

Every plugin declares one `PluginMetadata` (`devops_ai_toolkit.plugins.metadata`).
The **marketplace block** is exactly what an online registry would index; the
**capability block** tells the engine what inputs the plugin handles; the
**enterprise block** supports private, signed distribution (see
[enterprise plugins](enterprise-plugins.md)).

| Field | Block | Default | Purpose |
| --- | --- | --- | --- |
| `name` | marketplace | (required) | Unique plugin name, e.g. `docker`. |
| `version` | marketplace | `0.1.0` | Plugin version (semver). |
| `description` | marketplace | `""` | One-line summary for listings. |
| `author` | marketplace | `""` | Author / maintainer. |
| `homepage` | marketplace | `""` | Project homepage. |
| `repository` | marketplace | `""` | Source repository URL. |
| `documentation` | marketplace | `""` | Docs URL. |
| `license` | marketplace | `MIT` | SPDX license id. |
| `minimum_core_version` | marketplace | `0.1.0` | Lowest core version supported. |
| `tags` | marketplace | `[]` | Search/category tags. |
| `supported_platforms` | marketplace | `["linux","macos","windows"]` | OS platforms. |
| `supported_technologies` | capability | `[]` | `Technology` values it owns. |
| `supported_file_types` | capability | `[]` | File extensions, e.g. `[".log", ".yaml"]`. |
| `supported_commands` | capability | `[]` | CLI commands whose output it understands. |
| `builtin` | enterprise | `false` | True for plugins shipped with the core. |
| `signed` | enterprise | `false` | True when a verified checksum ships. |
| `checksum` | enterprise | `null` | Optional sha256 of the plugin payload. |

### As a YAML descriptor

A registry could index a plugin from a block like this (one-to-one with
`PluginMetadata`):

```yaml
name: docker
version: 1.2.0
description: Docker engine and container runtime error analysis.
author: DevOps AI Toolkit
homepage: https://devopsaitoolkit.com
repository: https://github.com/devopsaitoolkit/devops-ai-toolkit
documentation: https://devopsaitoolkit.com/docs/plugins
license: MIT
minimum_core_version: "0.1.0"
tags: [docker, containers, runtime]
supported_platforms: [linux, macos, windows]
supported_technologies: [docker]
supported_file_types: [".log"]
supported_commands: ["docker logs", "docker inspect"]
```

### As JSON (what the API already returns)

`GET /plugins/{name}` and `devops-ai plugins info <name>` emit precisely this
metadata, so a registry can ingest it straight from a published plugin:

```bash
devops-ai plugins info kubernetes
```

```json
{
  "name": "kubernetes",
  "version": "0.1.0",
  "description": "Kubernetes & OpenShift pod, scheduling, and manifest errors.",
  "author": "DevOps AI Toolkit",
  "homepage": "https://devopsaitoolkit.com",
  "repository": "https://github.com/devopsaitoolkit/devops-ai-toolkit",
  "documentation": "https://github.com/devopsaitoolkit/devops-ai-toolkit/blob/main/docs/plugins.md",
  "license": "MIT",
  "minimum_core_version": "0.1.0",
  "tags": ["kubernetes", "k8s", "openshift", "containers"],
  "supported_platforms": ["linux", "macos", "windows"],
  "supported_technologies": ["kubernetes", "openshift"],
  "supported_file_types": [".yaml", ".yml", ".log"],
  "supported_commands": ["kubectl describe", "kubectl logs", "kubectl get events"],
  "builtin": true,
  "signed": false,
  "checksum": null
}
```

---

## How a future registry installs without core changes

```
registry ──► resolves name/version + compatibility (minimum_core_version)
          ──► `pip install <plugin>` (or internal index)
          ──► entry point `devops_ai_toolkit.plugins` is registered by pip
          ──► engine auto-discovers on next run; `plugins doctor` confirms health
```

1. **Compatibility is checked before listing and again at load.** The registry can
   filter by `minimum_core_version` up front; the engine re-verifies via
   `is_compatible()` at discovery, so an incompatible plugin degrades to a
   *failure* rather than breaking anything.
2. **Install is just packaging.** Any installer that lands the distribution on
   `sys.path` makes the entry point visible — public PyPI, a private index, or a
   wheel file all work identically.
3. **No core release is coupled to a plugin release.** Plugins version
   independently and declare their own floor, so the registry never has to wait on
   a core change to publish.

---

## Publishing a marketplace-ready plugin

Fill in the full marketplace block (don't leave `description`, `homepage`,
`repository`, `documentation`, `tags` blank), pick an SPDX `license`, and set
`minimum_core_version` to the oldest core you actually support. Then build and
publish per [plugin development](plugin-development.md). The richer the metadata,
the better your plugin indexes and the easier it is to vet.

---

## See also

- [Plugins](plugins.md) — discovery, lifecycle, CLI/REST.
- [Plugin development](plugin-development.md) — scaffold, package, publish.
- [Enterprise plugins](enterprise-plugins.md) — `signed`/`checksum`, private indexes, the trust model.
