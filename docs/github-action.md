# GitHub Action (planned)

> **Status: planned / design note.** This describes a future surface. It is not yet released. The
> design reuses the existing [SDK](sdk-guide.md) and [CLI](cli-guide.md) — no new analysis logic.

## Goal

Bring read-only analysis into CI: when a workflow produces logs or changes manifests, analyze them
and surface ranked root causes and read-only diagnostics right in the PR or job summary.

## Proposed usage

```yaml
name: devops-ai
on: [pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Validate manifests
        uses: devopsaitoolkit/devops-ai-action@v1
        with:
          command: validate
          path: k8s/**/*.yaml

      - name: Analyze failing test logs
        if: failure()
        uses: devopsaitoolkit/devops-ai-action@v1
        with:
          command: analyze
          path: build/test.log
          tech: kubernetes
```

## Proposed inputs

| Input      | Description                                              | Default          |
|------------|---------------------------------------------------------|------------------|
| `command`  | `analyze` \| `explain` \| `validate`                    | `analyze`        |
| `path`     | File or glob to read                                     | —                |
| `tech`     | Technology hint                                         | auto-detect      |
| `enrich`   | Add LLM narrative (requires a provider secret)          | `false`          |
| `provider` | `anthropic` \| `openai` \| `gemini` \| `ollama`         | configured       |
| `fail-on`  | `none` \| `match` \| `invalid`                          | `none`           |

## Proposed behaviour

- Runs entirely **offline** by default — no secrets required for deterministic analysis.
- Writes a Markdown report to the **job summary** (`$GITHUB_STEP_SUMMARY`) and, optionally,
  annotations on changed lines.
- `fail-on: invalid` fails the job when `validate` finds errors; `fail-on: match` fails when a
  known failure signature is detected (handy for blocking known-bad patterns).
- Enrichment is opt-in and reads a provider key from repository secrets, e.g.
  `ANTHROPIC_API_KEY`. See [Configuration](configuration.md) and [Security](security.md).

## Implementation sketch

A composite action that installs the package and shells out to the CLI with `--json`, then formats
the result for the job summary:

```bash
pip install devops-ai-toolkit
devops-ai "$COMMAND" "$PATH" ${TECH:+--tech $TECH} --json > result.json
python format_summary.py result.json >> "$GITHUB_STEP_SUMMARY"
```

Because it's built on the [shared engine](architecture.md), output matches the CLI, SDK, and API
exactly.

## Feedback

Want this sooner, or have requirements? Open an issue (see [Contributing](contributing.md)) or
follow <https://devopsaitoolkit.com/blog>.
