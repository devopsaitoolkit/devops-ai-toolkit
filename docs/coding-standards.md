# Coding standards

Conventions enforced in the codebase. They keep the engine small, typed, and read-only.

## Tooling

| Concern   | Tool   | Command               |
|-----------|--------|-----------------------|
| Lint      | Ruff   | `ruff check .`        |
| Format    | Ruff   | `ruff format .`       |
| Types     | mypy   | `mypy src`            |
| Tests     | pytest | `pytest`              |
| Hooks     | pre-commit | `pre-commit run -a` |

Configuration lives in `pyproject.toml`.

## Python version and style

- Target **Python 3.12+**. Use modern syntax: `X | None` unions, `list[str]`, `from __future__
  import annotations` at the top of modules.
- **Line length: 100.**
- Ruff rule sets enabled: `E`, `F`, `I` (imports), `UP` (pyupgrade), `B` (bugbear), `C4`, `SIM`,
  `RUF`, `N` (naming), `D` (pydocstyle, **Google** convention). Ignored: `D203`, `D213`, `D401`,
  `B008`.

## Typing

- mypy runs in **strict** mode (with the `pydantic.mypy` plugin). Type everything in `src/`.
- Tests and examples relax untyped-def rules, but prefer types there too.
- Prefer precise models over `dict`/`Any`. The data contracts are Pydantic models in `models/`.

## Docstrings

- Every module, public class, and public function has a docstring (Google style).
- Document the *why* and any read-only guarantees, as the existing modules do (see the engine and
  provider modules for the tone).

## Architecture rules

- **Business logic only in the engine.** Interfaces (`cli/`, `api/`, SDK surface) stay thin. See
  [Architecture](architecture.md).
- **Depend on protocols, not vendors.** Never import a vendor SDK in core code; go through the
  `AIProvider` protocol and the registry. See [AI providers](ai-providers.md).
- **Pure helpers.** Prefer small, module-level pure functions (easy to test) over hidden state, as
  in the engine's de-dupe/split helpers.
- **Additive contracts.** Grow `AnalysisResult` by adding fields; don't break serialization.

## Read-only discipline

- No code path may execute external commands or mutate files/infrastructure.
- `DiagnosticCommand.read_only` is always `true`; only suggest non-mutating commands.
- Validation and analysis inspect text only. See [Security](security.md).

## Error handling

- Providers must construct safely when unconfigured and report readiness via `available()`.
- Network/provider failures must degrade gracefully (log + deterministic fallback), never crash an
  analysis.
- Validate external data (e.g. signature regexes) at load time and fail fast on malformed input.

## Naming and structure

- Follow PEP 8 / Ruff `N` rules. Signature ids are stable, dotted, and lowercase (e.g.
  `k8s.oomkilled`).
- Keep modules focused on one responsibility; mirror the package layout in
  [Developer guide](developer-guide.md).

## Commits and PRs

See [Contributing](contributing.md) for the PR checklist and commit style.
