# Knowledge base

The knowledge base is the heart of the toolkit's offline, deterministic analysis. It is a set of
**signatures** — declarative YAML rules that match patterns in an input and yield ranked root
causes, read-only diagnostic commands, suggested fixes, references, and prevention advice. Because
signatures are data, contributors can add coverage **without touching engine code**.

## Where signatures live

```
src/devops_ai_toolkit/knowledge/data/*.yaml
```

One file per technology area, for example: `kubernetes.yaml`, `terraform.yaml`, `docker.yaml`,
`openstack.yaml`, `linux.yaml`, `systemd.yaml`, `nginx.yaml`, `postgresql.yaml`, `mysql.yaml`,
`redis.yaml`, `rabbitmq.yaml`, `prometheus.yaml`, `ceph.yaml`, `ansible.yaml`, `gitlab_ci.yaml`,
`aws.yaml`, `azure_gcp.yaml`. See [Supported technologies](supported-technologies.md).

List what's installed:

```bash
devops-ai list
devops-ai list --tech kubernetes
```

## How matching works

`SignatureMatcher` evaluates each signature's `match` block against the input:

- Patterns are **case-insensitive regular expressions**.
- `any_of`: the signature fires if **any** pattern matches (logical OR).
- `all_of`: **every** pattern here must also match (logical AND) — use it to disambiguate
  look-alike errors.
- `weight` (0.0–1.0) is the base confidence when the signature matches.

Each match also captures **evidence**: the trimmed source lines that matched, so findings are
justified back to the operator.

When building the result, the engine blends the signature's match score with each individual
cause's prior confidence, then ranks root causes highest-first and de-duplicates commands and
references. See [Architecture](architecture.md#the-analysis-pipeline).

## Signature schema

A single signature (one list item in a YAML data file):

```yaml
- id: k8s.crashloopbackoff           # required, stable unique id
  technology: kubernetes             # required, a Technology enum value
  title: "Pod in CrashLoopBackOff"   # required, short human title
  summary: >-                        # required, one-paragraph explanation
    A container starts, exits, and Kubernetes restarts it with exponential
    backoff. The pod never reaches a stable Running state.
  applies_to: [log, kubernetes_manifest, command_output, error_string]  # SourceKind values
  match:                             # required
    any_of:                          # OR patterns (case-insensitive regex)
      - "CrashLoopBackOff"
      - "Back-off restarting failed container"
    all_of: []                       # optional AND patterns
    weight: 0.8                      # base confidence (0.0-1.0)
  root_causes:                       # ranked candidate explanations
    - title: "Application exits immediately on startup"
      description: >-
        The container's main process crashes or returns non-zero right after start.
      confidence: 0.7                # prior confidence (0.0-1.0)
      category: application          # free-form grouping label
  diagnostic_commands:               # READ-ONLY commands a human can run
    - command: "kubectl describe pod <pod> -n <namespace>"
      explanation: "Shows recent events, restart count, last state and exit code."
      expected_output: "Last State: Terminated, Reason: Error, Exit Code: 1 plus Events."
      platform: "any kubectl client" # optional
  suggested_fixes:                   # guidance, never auto-applied
    - title: "Relax or delay the liveness probe"
      description: "Add initialDelaySeconds/failureThreshold so slow starts are not killed."
      snippet: |                     # optional config/code snippet
        livenessProbe:
          httpGet: { path: /healthz, port: 8080 }
          initialDelaySeconds: 20
  references:                        # supporting docs
    - title: "CrashLoopBackOff troubleshooting guide"
      url: "https://devopsaitoolkit.com/blog/kubernetes-error-crashloopbackoff"
      source: "devopsaitoolkit"      # optional provenance label
  warnings:                          # optional cautions surfaced to the operator
    - message: "Blindly raising limits can mask a real memory leak."
      severity: medium               # info|low|medium|high|critical
  best_practices:                    # optional list of strings
    - "Make containers fail fast and log the reason to stdout/stderr."
  prevention:                        # optional list of strings
    - "Validate required config/secrets in CI before deploy."
  tags: [pods, restart, probes]      # optional free-form tags
```

### Field reference

| Field                 | Required | Notes                                                          |
|-----------------------|:--------:|----------------------------------------------------------------|
| `id`                  | ✅       | Stable, unique, dotted (e.g. `k8s.oomkilled`)                  |
| `technology`          | ✅       | A `Technology` enum value (see [enums](glossary.md))          |
| `title`               | ✅       | Short human-readable title                                     |
| `summary`             | ✅       | One paragraph                                                  |
| `match`               | ✅       | `any_of` / `all_of` regex + `weight`                          |
| `applies_to`          | optional | `SourceKind` values; defaults to `[log]`                      |
| `root_causes`         | optional | Each with `title`, `description`, `confidence`, `category`     |
| `diagnostic_commands` | optional | Always read-only; `command`, `explanation`, optional fields    |
| `suggested_fixes`     | optional | `title`, `description`, optional `snippet`, `references`       |
| `references`          | optional | `title`, `url`, optional `source`                             |
| `warnings`            | optional | `message`, `severity`                                          |
| `best_practices`      | optional | List of strings                                                |
| `prevention`          | optional | List of strings                                                |
| `tags`                | optional | List of strings                                                |

## Adding a signature

1. Pick the right data file under `knowledge/data/` (or add a new one for a new technology).
2. Append a new list item following the schema above. Give it a unique `id`.
3. Keep regex patterns specific enough to avoid false positives; use `all_of` to disambiguate.
4. Make every diagnostic command **read-only** — this is a hard project rule. See
   [Security](security.md).
5. Prefer authoritative references; link a tutorial on
   <https://devopsaitoolkit.com/blog> when one exists.
6. Add a test that asserts your signature fires on a representative input. See the
   [Testing guide](testing-guide.md).

Validate locally:

```bash
devops-ai explain "<your error pattern>"
echo "<sample log line>" | devops-ai analyze -
```

Loading is automatic — the packaged data directory is shipped with the wheel and read by the
`KnowledgeBase` loader at startup. No engine code changes are needed.

## Custom knowledge bases (SDK)

You can build and inject your own `KnowledgeBase` for private signatures:

```python
from devops_ai_toolkit import AnalysisEngine
from devops_ai_toolkit.knowledge.loader import KnowledgeBase

kb = KnowledgeBase.from_yaml_dir("/path/to/my/signatures")
engine = AnalysisEngine(knowledge_base=kb)
```

See the [Plugin guide](plugin-guide.md) for a worked example.

## See also

- [Supported technologies](supported-technologies.md)
- [Output format](output-format.md) — how signature fields become result fields
- [Contributing](contributing.md) — submitting new signatures
