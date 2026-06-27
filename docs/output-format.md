# Output format

Every interface returns the **same** Pydantic models — the CLI renders them with Rich, the REST
API serializes them to JSON, and the SDK hands them back to you directly. This page is the field
reference for all three. The contract is **additive**: fields are added, not removed or renamed.

There are three top-level result types:

- [`AnalysisResult`](#analysisresult) — from `analyze*`
- [`ExplainResult`](#explainresult) — from `explain_error` / `/explain`
- [`ValidationResult`](#validationresult) — from `validate_manifest` / `/validate`

## AnalysisResult

| Field                 | Type                       | Description                                              |
|-----------------------|----------------------------|----------------------------------------------------------|
| `summary`             | `str`                      | One-line human summary of the analysis                   |
| `technology`          | `Technology`               | Detected or hinted technology                            |
| `source_kind`         | `SourceKind`               | Detected or hinted input shape                           |
| `signatures_matched`  | `list[str]`                | IDs of knowledge-base signatures that fired              |
| `root_causes`         | `list[RootCause]`          | Ranked candidate explanations (highest confidence first) |
| `diagnostic_commands` | `list[DiagnosticCommand]`  | Read-only commands to confirm a hypothesis               |
| `suggested_fixes`     | `list[SuggestedFix]`       | Remediation guidance (never auto-applied)                |
| `references`          | `list[Reference]`          | Supporting docs                                          |
| `warnings`            | `list[Warning]`            | Cautions (e.g. data-loss risk in a fix)                  |
| `best_practices`      | `list[str]`                | General good-practice advice                             |
| `prevention`          | `list[str]`                | How to stop it recurring                                 |
| `enrichment`          | `Enrichment \| null`       | Optional LLM narrative (only when `enrich` succeeded)    |
| `metadata`            | `dict[str, str]`           | Engine metadata (e.g. `engine`, `signatures_evaluated`) |

Computed (derived) fields, available on the model and in JSON:

| Computed field       | Type    | Description                                          |
|----------------------|---------|------------------------------------------------------|
| `confidence`         | `float` | Strongest single root-cause confidence (0.0 if none) |
| `confidence_percent` | `int`   | The above as a whole percentage                      |
| `matched`            | `bool`  | True if at least one root cause was found            |

### RootCause

| Field                | Type        | Description                                        |
|----------------------|-------------|----------------------------------------------------|
| `title`              | `str`       | Short cause title                                  |
| `description`        | `str`       | Explanation                                        |
| `confidence`         | `float`     | 0.0–1.0 likelihood this is the cause               |
| `category`           | `str`       | Grouping label (e.g. `application`, `network`)     |
| `evidence`           | `list[str]` | Input snippets that support this cause             |
| `confidence_percent` | `int`       | Computed: confidence as a whole percentage         |
| `confidence_band`    | `ConfidenceBand` | Computed bucket: `very_low`…`very_high`        |

Confidence bands map scores to buckets: `≥0.85` very_high, `≥0.65` high, `≥0.45` moderate,
`≥0.25` low, else very_low.

### DiagnosticCommand

| Field             | Type   | Description                                       |
|-------------------|--------|---------------------------------------------------|
| `command`         | `str`  | The read-only command to run                      |
| `explanation`     | `str`  | Why it helps and what it inspects                 |
| `expected_output` | `str`  | What a healthy/revealing result looks like        |
| `platform`        | `str`  | Where to run it (e.g. `control plane node`)       |
| `read_only`       | `bool` | **Always `true`** — the toolkit only suggests non-mutating commands |

### SuggestedFix

| Field         | Type              | Description                              |
|---------------|-------------------|------------------------------------------|
| `title`       | `str`             | Short fix title                          |
| `description` | `str`             | Guidance (never auto-applied)            |
| `snippet`     | `str`             | Optional config/code illustrating the fix |
| `references`  | `list[Reference]` | Optional supporting docs                 |

### Reference / Warning / Enrichment

```jsonc
// Reference
{ "title": "...", "url": "https://...", "source": "official docs" }

// Warning
{ "message": "...", "severity": "info|low|medium|high|critical" }

// Enrichment (present only when LLM enrichment ran)
{ "provider": "anthropic", "model": "claude-sonnet-4-6",
  "narrative": "...", "additional_causes": ["..."] }
```

### Example JSON (abridged)

```json
{
  "summary": "Most likely cause (75% confidence): Application exits immediately on startup. 3 candidate cause(s) identified for kubernetes.",
  "technology": "kubernetes",
  "source_kind": "log",
  "signatures_matched": ["k8s.crashloopbackoff"],
  "confidence": 0.75,
  "confidence_percent": 75,
  "matched": true,
  "root_causes": [
    {
      "title": "Application exits immediately on startup",
      "description": "The container's main process crashes or returns non-zero right after start.",
      "confidence": 0.75,
      "confidence_percent": 75,
      "confidence_band": "high",
      "category": "application",
      "evidence": ["Back-off restarting failed container app in pod web-7d9f"]
    }
  ],
  "diagnostic_commands": [
    {
      "command": "kubectl logs <pod> -n <namespace> --previous",
      "explanation": "Prints logs from the previous crashed container.",
      "expected_output": "The application's stack trace or fatal error message.",
      "platform": "",
      "read_only": true
    }
  ],
  "suggested_fixes": [{ "title": "Fix the startup failure ...", "description": "...", "snippet": "", "references": [] }],
  "references": [{ "title": "CrashLoopBackOff troubleshooting guide", "url": "https://devopsaitoolkit.com/blog/kubernetes-error-crashloopbackoff", "source": "devopsaitoolkit" }],
  "warnings": [],
  "best_practices": ["Make containers fail fast and log the reason to stdout/stderr."],
  "prevention": ["Validate required config/secrets in CI before deploy."],
  "enrichment": null,
  "metadata": { "engine": "deterministic", "signatures_evaluated": "42" }
}
```

## ExplainResult

| Field                 | Type                      | Description                          |
|-----------------------|---------------------------|--------------------------------------|
| `query`               | `str`                     | What you asked about                 |
| `technology`          | `Technology`              | Detected technology                  |
| `title`               | `str`                     | Signature title (or the query)       |
| `summary`             | `str`                     | Explanation                          |
| `root_causes`         | `list[RootCause]`         | Candidate causes                     |
| `diagnostic_commands` | `list[DiagnosticCommand]` | Read-only commands                   |
| `suggested_fixes`     | `list[SuggestedFix]`      | Remediation guidance                 |
| `references`          | `list[Reference]`         | Supporting docs                      |
| `best_practices`      | `list[str]`               | Good-practice advice                 |
| `matched`             | `bool`                    | False when no signature matched      |

When nothing matches, `matched` is `false` and `summary` suggests running `analyze` on the raw
input or browsing <https://devopsaitoolkit.com/blog>.

## ValidationResult

| Field            | Type                    | Description                                 |
|------------------|-------------------------|---------------------------------------------|
| `technology`     | `Technology`            | Detected technology                         |
| `source_kind`    | `SourceKind`            | Detected input shape                        |
| `valid`          | `bool`                  | Whether the document passed validation      |
| `issues`         | `list[ValidationIssue]` | Problems found                              |
| `best_practices` | `list[str]`             | Advisory recommendations                    |
| `error_count`    | `int` (computed)        | Number of high/critical-severity issues     |

### ValidationIssue

| Field      | Type           | Description                              |
|------------|----------------|------------------------------------------|
| `severity` | `Severity`     | `info`/`low`/`medium`/`high`/`critical`  |
| `message`  | `str`          | What's wrong                             |
| `line`     | `int \| null`  | Line number when known                  |
| `path`     | `str`          | Dotted path to the field when known     |
| `hint`     | `str`          | How to fix it                           |

## Serializing in code

```python
result = engine.analyze_file("app.log")
result.model_dump_json(indent=2)   # JSON string
result.model_dump()                # plain dict
```

On the CLI, add `--json` to any of `analyze`, `explain`, `validate` to get this JSON instead of the
Rich rendering. See the [CLI guide](cli-guide.md).
