# Enterprise plugins

The plugin architecture is built for environments that need **internal, private,
signed, and pinned** plugins installed **offline** from a controlled package
index. Nothing about enterprise distribution requires a special build of the
toolkit — the same `devops_ai_toolkit.plugins` entry point and the same
`PluginMetadata` schema cover it. This guide covers private plugins, the
`signed`/`checksum` fields, version pinning, dependency resolution, offline
installation, and the security/trust model.

Read [Plugins](plugins.md) and [plugin development](plugin-development.md) first.

---

## Internal and private plugins

An internal plugin is identical to a public one — it just isn't published to PyPI.
Scaffold it the same way:

```bash
devops-ai create-plugin acme-internal
```

Distribute the built wheel through your own channel (artifact store, internal
index, or a checked-in `dist/` directory). Once installed it is auto-discovered
via the entry point; `devops-ai plugins list` shows it with `source=entrypoint`.

Because **entry-point plugins override built-ins of the same name** (a logged
warning), an organisation can ship a hardened internal replacement for a built-in
plugin — e.g. an `acme` build of `kubernetes` with company-specific signatures —
without forking the core. See
[conflict resolution](plugins.md#conflict-resolution).

---

## Signed plugins and integrity

`PluginMetadata` carries two supply-chain fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `signed` | `bool` | True when the plugin ships a verified checksum. |
| `checksum` | `str \| None` | Optional sha256 of the plugin payload. |

```python
from devops_ai_toolkit.plugins import PluginMetadata
from devops_ai_toolkit.models.enums import Technology

METADATA = PluginMetadata(
    name="acme-internal",
    version="1.4.2",
    author="ACME Platform Security",
    license="Proprietary",
    minimum_core_version="0.1.0",
    supported_technologies=[Technology.UNKNOWN],
    signed=True,
    checksum="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
)
```

Use these to record provenance: compute the sha256 of the plugin payload at build
time, set `checksum`, and flip `signed=True`. Your installation/vetting pipeline
verifies the checksum before the wheel is allowed into the internal index, and the
field is visible in `plugins info` / `GET /plugins/{name}` for audit. Combine this
with package-level signing (e.g. wheel signing / Sigstore) on your private index
for end-to-end integrity.

---

## Version pinning

Pin both the plugin and the core for reproducible fleets:

```
# constraints.txt — enforce exact versions across the org
devops-ai-toolkit==0.1.0
acme-internal==1.4.2
```

```bash
pip install -c constraints.txt acme-internal
```

The plugin's own `minimum_core_version` is a *floor*, checked at load via
`is_compatible()`. Pinning in `constraints.txt` gives you an *exact* version on top
of that floor. If a pinned plugin is incompatible with the installed core, the
manager records a failure with the precise reason (`requires core >= X, have Y`)
instead of crashing.

---

## Dependency resolution

- Each plugin declares its own dependencies in `pyproject.toml`; pip resolves them
  at install time like any package.
- Keep a single shared core version across all installed plugins; declare wide,
  justified ranges so plugins co-install cleanly.
- Use a constraints file (above) to lock the resolved graph for your whole fleet.
- A plugin that can't import because of a missing/incompatible dependency is
  **isolated as a load failure**, not a crash — `devops-ai plugins doctor` reports
  exactly which plugin and why, so resolution problems are diagnosable.

---

## Offline installation

Plugins install in fully air-gapped environments because they are ordinary
wheels. Two common patterns:

**Local wheelhouse (no index at all):**

```bash
# On a connected host:
pip download acme-internal -d /tmp/wheelhouse
# Transfer /tmp/wheelhouse to the air-gapped host, then:
pip install --no-index --find-links /tmp/wheelhouse acme-internal
```

**Internal package index:**

```bash
pip install --index-url https://pypi.internal.acme/simple/ acme-internal
# or pin it for everyone:
#   PIP_INDEX_URL=https://pypi.internal.acme/simple/
```

After either, verify discovery and health:

```bash
devops-ai plugins list
devops-ai plugins doctor
```

---

## Enterprise / private package repositories

Host plugins on a private index (Artifactory, Nexus, devpi, GitHub/GitLab package
registries, AWS CodeArtifact, etc.). Configure pip once via `PIP_INDEX_URL` /
`PIP_EXTRA_INDEX_URL` or `pip.conf`, and your plugins install exactly like public
ones — the engine doesn't care where the wheel came from. Gate which plugins reach
the index with your vetting/signing pipeline (verify `checksum`, license, and
`minimum_core_version`).

`devops-ai plugins update` reminds users to update installed plugin packages and
lists the installed plugin distributions and their versions:

```bash
devops-ai plugins update
pip install -U acme-internal --index-url https://pypi.internal.acme/simple/
```

---

## Compatibility validation

Before rolling a plugin to the fleet, validate compatibility against the core
version you run:

```bash
devops-ai version           # the installed core version
devops-ai plugins doctor    # loaded/enabled counts + any incompatibilities
```

`doctor` returns the core version, how many plugins loaded and are enabled, the
total signatures, and a `failures` list with the reason for each — including
incompatibility (`requires core >= ...`). Wire `plugins doctor` into CI/golden-image
builds: it exits non-zero when there are failures, so a bad plugin fails the
pipeline rather than the production engine.

---

## The security / trust model

- **Read-only guarantee.** The toolkit inspects text and produces guidance. It
  never executes commands, mutates files, or touches infrastructure; the
  diagnostic commands plugins suggest are read-only by convention. Built-in
  plugins validate manifests read-only and only *suggest* commands — vet
  third-party plugins to the same standard.
- **Plugins run in-process (trust model).** Discovered plugins are imported and
  executed inside the host Python process — there is no sandbox. A plugin you
  install has the same privileges as the toolkit itself. **Only install plugins
  you trust**, exactly as you would any Python dependency. For untrusted code,
  isolate the whole toolkit (dedicated venv, container, restricted service
  account).
- **Isolation of failures, not of trust.** Load isolation means a broken or
  incompatible plugin becomes a recorded *failure* rather than crashing the
  engine — it does not make an untrusted plugin safe to run. Use `signed`/
  `checksum` plus your private index's signing to establish *who* produced a
  plugin; use `plugins doctor` to confirm *what* loaded.
- **How to vet and sign.** Review the plugin's signatures and any validator for
  read-only behaviour; confirm `license` and `author`; compute and pin a
  `checksum` and set `signed=True`; publish only to a controlled internal index;
  pin exact versions via constraints; and run `plugins doctor` in CI.

---

## See also

- [Plugins](plugins.md) — discovery, lifecycle, conflict resolution, CLI/REST.
- [Plugin development](plugin-development.md) — building and packaging.
- [Plugin marketplace](plugin-marketplace.md) — the metadata schema (incl. `signed`/`checksum`).
- [Security](security.md) — the toolkit's overall read-only and key-handling guarantees.
