# Troubleshooting guide

Problems with the toolkit itself and how to fix them. (For troubleshooting *your* infrastructure,
that's what the toolkit is for — see [Use cases](use-cases.md).)

## Installation

### `devops-ai: command not found`

The console script isn't on your `PATH`. Confirm the install and your environment:

```bash
pip show devops-ai-toolkit
python -m pip install --user devops-ai-toolkit   # if installing per-user
```

If you installed into a virtualenv, make sure it's activated. You can always invoke via the module
entry indirectly through the SDK, or reinstall in the active environment.

### `Install the API extra: pip install 'devops-ai-toolkit[api]'`

`devops-ai serve` needs FastAPI + Uvicorn, which ship as the optional `api` extra:

```bash
pip install 'devops-ai-toolkit[api]'
```

### `requires-python` / Python version error

The toolkit needs **Python 3.12+**. Check with `python --version` and use a 3.12 interpreter.

## Analysis

### "No known … error signature matched"

The input was read but didn't match a catalogued pattern. Options:

- Add a `--tech` hint so detection isn't the issue: `devops-ai analyze app.log --tech kubernetes`.
- Provide more of the raw log rather than a paraphrase.
- The pattern may simply not be in the knowledge base yet — consider
  [adding a signature](knowledge-base.md#adding-a-signature), or browse
  <https://devopsaitoolkit.com/blog>.

### "No input. Pass a file path or pipe content via stdin."

`analyze`/`validate` got nothing. Either pass a file path or pipe content and use `-`:

```bash
devops-ai analyze app.log
cat app.log | devops-ai analyze -
```

### `File not found`

The path argument doesn't exist. Check the path; exit code is `2` for input errors.

### Output looks truncated

Inputs are truncated to `DEVOPS_AI_MAX_CHARS` (default 200,000). Raise it if you must analyze
larger text:

```bash
export DEVOPS_AI_MAX_CHARS=500000
```

See [Configuration](configuration.md).

## Exit codes

| Code | Meaning                                    |
|------|--------------------------------------------|
| `0`  | Matched / valid                            |
| `1`  | No match / validation failed               |
| `2`  | Input error (missing file, empty stdin)    |

If a script "fails" on a clean run, remember `analyze` exits `1` when nothing matched — that's a
valid outcome, not an error.

## AI enrichment

### Enrichment was skipped

You passed `--enrich` / `enrich=True` but no provider is available, so you got a low-severity
warning and deterministic-only results. Set a provider and its key:

```bash
export DEVOPS_AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

Check readiness via the API:

```bash
curl -s localhost:8000/health | jq '{provider, provider_available}'
```

See [AI providers](ai-providers.md).

### Provider/network errors

If a provider call fails, the engine logs a warning and returns the deterministic result — analysis
is never broken by an LLM failure. Verify the key, model name, network/proxy, and
`DEVOPS_AI_TIMEOUT`.

### Wrong model is being used

Override per provider, e.g. `DEVOPS_AI_ANTHROPIC_MODEL`, `DEVOPS_AI_OPENAI_MODEL`,
`DEVOPS_AI_GEMINI_MODEL`, `DEVOPS_AI_OLLAMA_MODEL`. See [Configuration](configuration.md).

## REST API

### Can't reach the server

Defaults to `127.0.0.1:8000`. To accept remote connections bind to `0.0.0.0`:

```bash
devops-ai serve --host 0.0.0.0 --port 8000
```

Remember the API ships no auth — front it with your own. See [Security](security.md).

### Where are the docs?

Swagger UI at `/docs`, ReDoc at `/redoc`, OpenAPI JSON at `/openapi.json`.

## Still stuck?

- Browse guides at <https://devopsaitoolkit.com/blog>
- Open an issue on the repository (see [Contributing](contributing.md))
