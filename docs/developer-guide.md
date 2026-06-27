# Developer guide

How the codebase is laid out and how to work in it productively. Read
[Architecture](architecture.md) first for the big picture.

## Environment

The project uses [`uv`](https://github.com/astral-sh/uv) for development.

```bash
git clone https://github.com/devopsaitoolkit/devops-ai-toolkit
cd devops-ai-toolkit

uv venv
uv pip install -e '.[all]'   # editable install with api + dev extras
pre-commit install
```

Targets **Python 3.12+**. Build backend is `hatchling`. The packaged knowledge-base data directory
(`knowledge/data`) is force-included in the wheel.

## Repository layout

```
src/devops_ai_toolkit/
├── analysis/      # AnalysisEngine — the ONLY place with business logic
├── models/        # Pydantic models (analysis, knowledge) + enums
├── knowledge/     # YAML signature data + KnowledgeBase loader
├── detectors/     # SignatureMatcher (regex + scoring)
├── analyzers/     # source-kind/technology augmenters
├── validators/    # read-only YAML / Kubernetes / Terraform validation
├── parsers/       # YAML-doc and Terraform parsing helpers
├── providers/     # AIProvider protocol, registry, per-vendor adapters
├── prompts/       # enrichment prompt templates
├── explainers/    # ErrorCatalog over the knowledge base
├── output/        # Rich console rendering + JSON serialization
├── cli/           # Typer app (devops-ai)
├── api/           # FastAPI app + request/response schemas
└── utils/         # settings, logging, text helpers
tests/             # pytest suite
docs/              # this documentation
```

## How a request flows

`AnalysisEngine.analyze()`:

1. Truncate input to `settings.max_input_chars`.
2. Detect technology and source kind (unless hinted).
3. `SignatureMatcher.match()` against the `KnowledgeBase`.
4. `_build_result()` blends scores, ranks root causes, de-dupes commands/references.
5. Optional source-kind/technology `analyzer.augment()`.
6. Optional `_maybe_enrich()` when `enrich=True` and a provider is available.

See [Architecture](architecture.md#the-analysis-pipeline).

## Key collaborators (all injectable)

The engine takes three optional dependencies, which makes it trivial to test and customize:

```python
AnalysisEngine(
    knowledge_base=...,  # KnowledgeBase
    provider=...,        # AIProvider
    settings=...,        # Settings
)
```

- `KnowledgeBase` — loaded from packaged YAML by default; override for custom signatures.
- `AIProvider` — resolved from the registry; defaults to offline `NullProvider`.
- `Settings` — environment-derived; override to bypass env vars. See [Configuration](configuration.md).

## Adding behaviour

| Goal                                | Where                                  | Doc                                    |
|-------------------------------------|----------------------------------------|----------------------------------------|
| New error coverage                  | `knowledge/data/*.yaml`                | [Knowledge base](knowledge-base.md)    |
| New AI backend                      | a provider + `register_provider()`     | [AI providers](ai-providers.md)        |
| New analysis logic                  | `analysis/engine.py` (+ analyzers)     | [Architecture](architecture.md)        |
| New result field                    | `models/analysis.py` (additive)        | [Output format](output-format.md)      |
| New validation rule                 | `validators/`                          | [Knowledge base](knowledge-base.md)    |

Never put logic in `cli/`, `api/`, or the SDK surface — keep them thin.

## Local checks

```bash
ruff check .             # lint
ruff format .            # format
mypy src                 # types (strict)
pytest                   # tests
pytest --cov             # with coverage
```

See [Coding standards](coding-standards.md) and the [Testing guide](testing-guide.md).

## Running the interfaces locally

```bash
devops-ai analyze tests/fixtures/crashloop.log   # CLI
python -c "from devops_ai_toolkit import AnalysisEngine; print(AnalysisEngine().analyze_text('OOMKilled').summary)"
devops-ai serve --port 8000                       # API (needs the api extra)
```

## See also

- [Plugin guide](plugin-guide.md) — custom providers and signatures, end to end
- [Testing guide](testing-guide.md)
- [Release process](release-process.md)
