# CLI guide

The `devops-ai` command is a thin [Typer](https://typer.tiangolo.com/) wrapper over the shared
[`AnalysisEngine`](architecture.md). All real work happens in the engine; the CLI only handles
input/output and rendering.

```bash
devops-ai --help
```

## Commands at a glance

| Command                       | Purpose                                                   |
|-------------------------------|-----------------------------------------------------------|
| `devops-ai analyze <file>`    | Analyze a log, manifest, Terraform file, or output        |
| `devops-ai explain <error>`   | Explain a known error from the knowledge base             |
| `devops-ai validate <file>`   | Validate a YAML / Kubernetes / Terraform document         |
| `devops-ai list`              | List the error signatures the toolkit knows about         |
| `devops-ai serve`             | Run the FastAPI REST API (needs the `api` extra)          |
| `devops-ai version`           | Print the installed version                               |

## `analyze`

Analyze a file, or pipe content via stdin using `-`.

```bash
devops-ai analyze nova.log
kubectl get pods | devops-ai analyze -
cat terraform-apply.txt | devops-ai analyze -
```

Options:

| Option              | Description                                                          |
|---------------------|----------------------------------------------------------------------|
| `--tech`, `-t`      | Technology hint, e.g. `kubernetes`, `terraform`, `openstack`         |
| `--enrich`          | Add an LLM narrative (requires a configured provider)                |
| `--provider`        | Override the provider: `anthropic` \| `openai` \| `gemini` \| `ollama` |
| `--json`            | Emit machine-readable JSON instead of the Rich rendering             |

Examples:

```bash
devops-ai analyze app.log --tech kubernetes
devops-ai analyze app.log --json | jq '.root_causes[0]'
devops-ai analyze app.log --enrich --provider anthropic
```

**Exit code:** `0` if at least one signature/root cause matched, `1` if nothing matched, `2` on
input errors (missing file, empty stdin). This makes it easy to gate CI steps on a match.

## `explain`

Explain a named error without any input file.

```bash
devops-ai explain CrashLoopBackOff
devops-ai explain "exit code 137"
devops-ai explain ImagePullBackOff --json
```

Returns the title, summary, root causes, diagnostic commands, fixes, references, and best
practices for the best-matching signature. Exit code `0` when matched, `1` otherwise.

## `validate`

Read-only validation of a manifest or Terraform file. It never applies anything.

```bash
devops-ai validate deploy.yaml
cat deploy.yaml | devops-ai validate -
devops-ai validate main.tf --json
```

Exit code `0` when valid, `1` when validation issues are present. See
[Output format](output-format.md#validationresult) for the issue structure.

## `list`

Show the signatures in the knowledge base, optionally filtered by technology.

```bash
devops-ai list
devops-ai list --tech kubernetes
devops-ai list -t terraform
```

## `serve`

Start the REST API (requires `pip install 'devops-ai-toolkit[api]'`).

```bash
devops-ai serve                       # 127.0.0.1:8000 by default
devops-ai serve --host 0.0.0.0 --port 8080
```

See the [REST API guide](rest-api-guide.md).

## `version`

```bash
devops-ai version
```

## Piping and composition

Because `analyze` and `validate` accept stdin (`-`) and support `--json`, the CLI composes well
with standard tooling:

```bash
# Triage the most recent crashed pod's previous logs
kubectl logs my-pod --previous | devops-ai analyze - --tech kubernetes

# Fail a CI job if a Terraform plan trips a known error
terraform plan 2>&1 | devops-ai analyze - --tech terraform || echo "known issue detected"

# Extract just the top suggested fix as JSON
devops-ai analyze app.log --json | jq -r '.suggested_fixes[0].title'
```

## Configuration

The CLI honours the same environment variables as the rest of the toolkit (provider selection,
API keys, timeouts, input size). See [Configuration](configuration.md).

## See also

- [SDK guide](sdk-guide.md) — same engine, programmatic
- [Output format](output-format.md) — what each section means
- More walkthroughs at <https://devopsaitoolkit.com/blog>
