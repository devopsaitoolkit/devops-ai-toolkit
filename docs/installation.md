# Installation

The toolkit targets **Python 3.12+** and has a small, well-known dependency set. The core install
is fully offline — no API key and no network access are required to analyze input.

## Requirements

- Python **3.12 or newer**
- `pip` (or [`uv`](https://github.com/astral-sh/uv) for development)
- No external services required for the deterministic engine

## Core install (CLI + SDK)

```bash
pip install devops-ai-toolkit
```

This installs:

- the `devops-ai` command-line tool (see the [CLI guide](cli-guide.md))
- the `devops_ai_toolkit` Python package (see the [SDK guide](sdk-guide.md))
- the packaged YAML knowledge base (see [Knowledge base](knowledge-base.md))

Core runtime dependencies: `pydantic`, `pyyaml`, `typer`, `rich`, `jinja2`, `requests`.

## REST API extra

The HTTP server (FastAPI + Uvicorn) ships as an optional extra so the core stays lightweight:

```bash
pip install 'devops-ai-toolkit[api]'
```

Then start it with either:

```bash
devops-ai serve --host 0.0.0.0 --port 8000
# or directly
uvicorn devops_ai_toolkit.api.app:app --host 0.0.0.0 --port 8000
```

See the [REST API guide](rest-api-guide.md).

## Verify the install

```bash
devops-ai version
devops-ai list           # prints the signatures the toolkit knows about
```

```python
import devops_ai_toolkit
print(devops_ai_toolkit.__version__)
```

## Optional AI provider dependencies

The toolkit talks to LLM providers over plain HTTP using `requests` — there is **no required
vendor SDK**. You only need to set the relevant environment variables:

| Provider  | Required variable      |
|-----------|------------------------|
| Anthropic | `ANTHROPIC_API_KEY`    |
| OpenAI    | `OPENAI_API_KEY`       |
| Gemini    | `GEMINI_API_KEY`       |
| Ollama    | `OLLAMA_HOST` (local)  |

Details in [Configuration](configuration.md) and [AI providers](ai-providers.md).

## Development install (with `uv`)

For contributing, clone the repo and use `uv` to create an environment with the `dev` (and
optionally `api`) extras:

```bash
git clone https://github.com/devopsaitoolkit/devops-ai-toolkit
cd devops-ai-toolkit

uv venv
uv pip install -e '.[all]'    # api + dev extras
```

The `dev` extra brings in `pytest`, `pytest-cov`, `ruff`, `mypy`, `pre-commit`, and `httpx`.
See the [Developer guide](developer-guide.md) and [Testing guide](testing-guide.md).

## Uninstall

```bash
pip uninstall devops-ai-toolkit
```

## Troubleshooting installs

If a command is missing or the API extra won't import, see the
[Troubleshooting guide](troubleshooting-guide.md).
