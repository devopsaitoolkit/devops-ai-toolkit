# Contributing

Thanks for helping improve the DevOps AI Toolkit. Contributions of all sizes are welcome — new
signatures, bug fixes, docs, providers, and features.

## Ground rules

1. **Read-only is non-negotiable.** No contribution may make the toolkit execute commands or mutate
   infrastructure. Diagnostic commands must always be non-mutating. See [Security](security.md).
2. **Logic lives in the engine.** The CLI, SDK, and API are thin adapters. New behaviour belongs in
   `AnalysisEngine`, not in an interface. See [Architecture](architecture.md).
3. **Contracts are additive.** Extend `AnalysisResult` and friends by adding fields, not renaming
   or removing them.

## Easiest contribution: a new signature

The highest-value, lowest-friction contribution is adding an error **signature** — it's just YAML,
no engine code. See [Knowledge base](knowledge-base.md#adding-a-signature). Steps:

1. Add a list item to the right file under `src/devops_ai_toolkit/knowledge/data/`.
2. Use a unique `id`, specific regex patterns, and **read-only** diagnostic commands.
3. Add a test asserting it fires on a representative input.
4. Open a PR.

## Setup

```bash
git clone https://github.com/devopsaitoolkit/devops-ai-toolkit
cd devops-ai-toolkit

uv venv
uv pip install -e '.[all]'   # api + dev extras
pre-commit install
```

See the [Developer guide](developer-guide.md).

## Before you open a PR

Run the local checks (see the [Testing guide](testing-guide.md) and
[Coding standards](coding-standards.md)):

```bash
ruff check .
ruff format --check .
mypy src
pytest
```

## Pull request checklist

- [ ] Behaviour change lives in the engine, not an interface
- [ ] Nothing executes commands or mutates state (read-only preserved)
- [ ] New/changed code has tests; `pytest` passes
- [ ] `ruff` and `mypy` are clean
- [ ] Public API changes are additive and documented under `docs/`
- [ ] New signatures have a unique `id`, references, and a test

## Commit and PR style

- Small, focused PRs are easier to review.
- Write a clear title and description; link related issues.
- Update the relevant docs in `docs/` when behaviour or APIs change.

## Reporting bugs

Open an issue with: the toolkit version (`devops-ai version`), the input (redacted), the command or
code you ran, and what you expected vs. got.

## Security issues

Report privately via the repository's security advisories rather than a public issue. See
[Security](security.md).

## Code of conduct

Be respectful and constructive. We want this to be a welcoming project for operators and developers
alike.

## See also

- [Developer guide](developer-guide.md)
- [Coding standards](coding-standards.md)
- [Release process](release-process.md)
- Stay in the loop: <https://devopsaitoolkit.com/newsletter>
