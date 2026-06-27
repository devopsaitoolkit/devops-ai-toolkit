# Contributing to devops-ai-toolkit

Thanks for your interest in contributing! This project is a **read-only** AI
DevOps troubleshooting engine (CLI + SDK + REST API) built on one shared
analysis engine. Contributions of all kinds are welcome: bug fixes, new
knowledge-base signatures, docs, and features.

By participating you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## The read-only rule (most important)

devops-ai-toolkit **never executes commands**, **never mutates** any system, and
**never transmits analyzed content** off the machine unless the user explicitly
enables an external AI provider (Anthropic, OpenAI, Gemini, or a self-hosted
Ollama endpoint). Every contribution must preserve this guarantee:

- Do not shell out to mutate infrastructure (no `apply`, `delete`, `restart`).
- Suggested "diagnostic commands" in the knowledge base must be read-only.
- The offline/deterministic core must work with no network access.

If a change cannot honor this, it does not belong in this project.

## Development setup

We use [uv](https://docs.astral.sh/uv/) for environment and dependency
management. Python **3.12+** is required.

```bash
# 1. Clone
git clone https://github.com/devopsaitoolkit/devops-ai-toolkit
cd devops-ai-toolkit

# 2. Create a virtual environment
uv venv

# 3. Install the package with all dev + api extras (editable)
uv pip install -e ".[all]"

# 4. Install pre-commit hooks
uv run pre-commit install
```

## Running checks

All checks mirror CI. Run them before pushing:

```bash
uv run ruff check .            # lint
uv run ruff format .           # format (use --check in CI)
uv run mypy src                # strict type checking
uv run pytest                  # tests
uv run pytest --cov=devops_ai_toolkit --cov-report=term-missing  # with coverage
```

You can run everything at once via pre-commit:

```bash
uv run pre-commit run --all-files
```

## Adding a knowledge-base signature

The deterministic knowledge base is the heart of the offline engine. To propose
or add a new error signature:

1. Read [`docs/knowledge-base.md`](docs/knowledge-base.md) for the schema and
   authoring conventions.
2. Add the signature data under
   `src/devops_ai_toolkit/knowledge/data/`.
3. Include: the **technology**, the **error string(s)** to match, the likely
   **root causes**, **read-only diagnostic commands**, and **references**.
4. Add a test that proves the signature matches its sample input.
5. Confirm all diagnostic commands are read-only.

Not ready to write code? Open a
[New knowledge-base signature](https://github.com/devopsaitoolkit/devops-ai-toolkit/issues/new?template=new_signature.yml)
issue instead and a maintainer can pick it up.

## Coding standards

- **Style & lint:** ruff (config in `pyproject.toml`, line length 100). Run
  `ruff format` before committing.
- **Types:** mypy in `strict` mode. New code must be fully typed; the package
  ships a `py.typed` marker.
- **Docstrings:** Google convention (enforced by ruff `D` rules) on public
  modules, classes, and functions.
- **Tests:** pytest under `tests/`. Add tests for every behavior change. Mark
  cross-interface end-to-end tests with `@pytest.mark.integration`.
- **No secrets** in code, tests, or fixtures.

## Pull request process

1. Fork and create a topic branch off `main`.
2. Make your change with tests and docs.
3. Ensure `ruff`, `mypy`, and `pytest` all pass locally.
4. Open a PR and fill out the template, including the read-only checklist.
5. A maintainer will review. Address feedback by pushing follow-up commits.
6. Squash-and-merge once approved and CI is green.

## Commit conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add OpenStack quota-exceeded signature
fix: handle empty Terraform plan input
docs: clarify SDK usage in README
chore: bump ruff to 0.5.7
test: cover Helm release error path
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `ci`.

## Reporting bugs and requesting features

Use the issue forms:
[bug report](https://github.com/devopsaitoolkit/devops-ai-toolkit/issues/new?template=bug_report.yml),
[feature request](https://github.com/devopsaitoolkit/devops-ai-toolkit/issues/new?template=feature_request.yml),
or [new signature](https://github.com/devopsaitoolkit/devops-ai-toolkit/issues/new?template=new_signature.yml).
For security issues, see [SECURITY.md](SECURITY.md) — do **not** open a public
issue.
