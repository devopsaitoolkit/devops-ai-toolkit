# Configuration

All configuration is sourced from the environment. **Nothing is required** for offline,
deterministic analysis — every setting has a safe default. Configuration is read once per process
and is dependency-light (no `pydantic-settings` requirement), so the core stays importable in
minimal environments.

## Core variables

| Variable               | Default                   | Purpose                                                       |
|------------------------|---------------------------|---------------------------------------------------------------|
| `DEVOPS_AI_PROVIDER`   | `null`                    | Active AI provider: `null`, `anthropic`, `openai`, `gemini`, `ollama` |
| `DEVOPS_AI_TIMEOUT`    | `60`                      | Provider HTTP request timeout, in seconds                     |
| `DEVOPS_AI_MAX_CHARS`  | `200000`                  | Max input characters analyzed (input is truncated above this) |

`null` is the offline default: the engine runs in pure deterministic mode and never calls out.

## Provider keys and models

| Variable               | Default                       | Purpose                                |
|------------------------|-------------------------------|----------------------------------------|
| `ANTHROPIC_API_KEY`    | _(unset)_                     | Anthropic API key                      |
| `OPENAI_API_KEY`       | _(unset)_                     | OpenAI API key                         |
| `GEMINI_API_KEY`       | _(unset)_                     | Gemini API key (`GOOGLE_API_KEY` also accepted) |
| `OLLAMA_HOST`          | `http://localhost:11434`      | Ollama server base URL (local, no key) |

A provider is considered *available* only when its key (or, for Ollama, its host) is present. If
you request enrichment without an available provider, the engine returns deterministic results and
adds a low-severity warning — it never fails. See [AI providers](ai-providers.md).

### Per-provider model and endpoint overrides

| Variable                     | Default                       |
|------------------------------|-------------------------------|
| `DEVOPS_AI_ANTHROPIC_MODEL`  | `claude-sonnet-4-6`           |
| `DEVOPS_AI_OPENAI_MODEL`     | `gpt-4o-mini`                 |
| `OPENAI_BASE_URL`            | `https://api.openai.com/v1`   |
| `DEVOPS_AI_GEMINI_MODEL`     | `gemini-2.0-flash`            |
| `DEVOPS_AI_OLLAMA_MODEL`     | `llama3.1`                    |

The `OPENAI_BASE_URL` override lets you point the OpenAI adapter at any OpenAI-compatible endpoint
(local gateways, proxies, alternative hosts).

### Alternative key names

For convenience these alternates are also recognized:

- `DEVOPS_AI_ANTHROPIC_KEY` → Anthropic key
- `DEVOPS_AI_OPENAI_KEY` → OpenAI key
- `DEVOPS_AI_GEMINI_KEY`, `GOOGLE_API_KEY` → Gemini key

## Examples

Offline (default — nothing to set):

```bash
devops-ai analyze app.log
```

Anthropic enrichment:

```bash
export DEVOPS_AI_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export DEVOPS_AI_ANTHROPIC_MODEL=claude-sonnet-4-6   # optional override
devops-ai analyze app.log --enrich
```

Local, fully private LLM via Ollama:

```bash
export DEVOPS_AI_PROVIDER=ollama
export OLLAMA_HOST=http://localhost:11434
export DEVOPS_AI_OLLAMA_MODEL=llama3.1
devops-ai analyze app.log --enrich
```

OpenAI-compatible gateway:

```bash
export DEVOPS_AI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://my-gateway.internal/v1
```

Tighten resource limits:

```bash
export DEVOPS_AI_MAX_CHARS=50000   # analyze at most 50k chars
export DEVOPS_AI_TIMEOUT=30        # 30s provider timeout
```

## Settings in code (SDK)

You can bypass the environment entirely by constructing `Settings` and injecting them:

```python
from devops_ai_toolkit import AnalysisEngine
from devops_ai_toolkit.utils.config import Settings

settings = Settings(provider="anthropic", anthropic_api_key="sk-ant-...", max_input_chars=50_000)
engine = AnalysisEngine(settings=settings)
```

`Settings.from_env()` builds the same object from a dict of environment variables, which is useful
in tests. See the [Testing guide](testing-guide.md).

## Precedence

1. Explicit arguments (e.g. CLI `--provider`, SDK `provider=`/`settings=`)
2. Environment variables
3. Built-in defaults (offline `null` provider)

## See also

- [AI providers](ai-providers.md) — adapter details and how to add one
- [Security](security.md) — how keys are handled (read from env, sent only to the chosen provider)
