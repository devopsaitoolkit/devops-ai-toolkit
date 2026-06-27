# Release process

How a maintainer cuts a release of `devops-ai-toolkit`. The package is built with `hatchling` and
versioned with semantic versioning.

## Versioning

- **SemVer**: `MAJOR.MINOR.PATCH`.
  - **MAJOR** — incompatible API changes (rare; the result contract is meant to be additive).
  - **MINOR** — new signatures, providers, features, or additive fields.
  - **PATCH** — bug fixes and doc-only changes.
- The version is declared in `pyproject.toml` (`[project].version`) and exposed at runtime as
  `devops_ai_toolkit.__version__` (and via `devops-ai version`, `/version`, and `/health`).

Adding new signatures or a new provider is a **minor** release. Removing or renaming a result field
would be **major** — avoid it; prefer additive changes (see [Coding standards](coding-standards.md)).

## Pre-release checklist

```bash
ruff check .
ruff format --check .
mypy src
pytest
```

- [ ] All checks green
- [ ] `CHANGELOG` updated (notable changes, new signatures, new providers)
- [ ] `docs/` updated for any behaviour or API change
- [ ] Version bumped in `pyproject.toml`
- [ ] New signatures have tests and references

## Build

```bash
uv build            # produces sdist + wheel in dist/
```

The wheel force-includes the packaged knowledge-base data (`knowledge/data`) per `pyproject.toml`,
so signatures ship with the package. Verify the data is present in the built wheel before
publishing.

## Smoke test the artifact

In a clean environment:

```bash
pip install dist/devops_ai_toolkit-*.whl
devops-ai version
devops-ai list                  # confirms packaged signatures load
devops-ai explain CrashLoopBackOff

pip install 'dist/devops_ai_toolkit-*.whl[api]'
devops-ai serve &              # then curl /health and /version
```

## Publish

```bash
# Recommended: validate on TestPyPI first
uv publish --repository testpypi

# Then production
uv publish
```

(Or use `twine upload dist/*` if that's your workflow.)

## Tag and announce

```bash
git tag -a vX.Y.Z -m "vX.Y.Z"
git push origin vX.Y.Z
```

- Create a GitHub Release with the changelog.
- Announce notable releases via <https://devopsaitoolkit.com/newsletter> and
  <https://devopsaitoolkit.com/blog>.

## Post-release

- Confirm `pip install devops-ai-toolkit==X.Y.Z` works from PyPI.
- Open the next development cycle (bump to the next dev version if you use one).

## See also

- [Contributing](contributing.md)
- [Roadmap](roadmap.md)
