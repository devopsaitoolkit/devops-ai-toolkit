# Testing guide

The toolkit is built for testability: the engine is a stateless façade with injectable
collaborators, and most logic is small pure functions. Tests use **pytest**.

## Running tests

```bash
pytest                  # whole suite
pytest -q               # quiet
pytest tests/test_engine.py::test_crashloop   # a single test
pytest -m integration   # only end-to-end cross-interface tests
pytest --cov            # with coverage (branch coverage is on)
```

pytest config lives in `pyproject.toml`: `testpaths = ["tests"]`, strict markers, and an
`integration` marker for end-to-end tests across interfaces.

## Dependencies

The `dev` extra installs `pytest`, `pytest-cov`, `httpx` (for API tests), plus `ruff` and `mypy`.

```bash
uv pip install -e '.[dev]'   # or '.[all]' for api too
```

## Testing the engine

Because every collaborator is injectable, you can test in isolation without touching the network or
the packaged data:

```python
from devops_ai_toolkit import AnalysisEngine

def test_crashloop_matches():
    engine = AnalysisEngine()
    result = engine.analyze_text("Back-off restarting failed container")
    assert result.matched
    assert "k8s.crashloopbackoff" in result.signatures_matched
    assert result.root_causes[0].confidence_percent > 0
```

### Deterministic by default

The default provider is the offline `NullProvider`, so engine tests are deterministic and
network-free. Don't enable enrichment in unit tests.

## Testing enrichment with a fake provider

Inject a fake that satisfies the `AIProvider` protocol — no real API call:

```python
from devops_ai_toolkit import AnalysisEngine
from devops_ai_toolkit.providers.base import CompletionRequest

class FakeProvider:
    name = "fake"
    model = "fake-1"
    def available(self) -> bool:
        return True
    def complete(self, request: CompletionRequest) -> str:
        return "Narrative here.\nCAUSE: an extra hypothesis"

def test_enrichment_attaches_narrative():
    engine = AnalysisEngine(provider=FakeProvider())
    result = engine.analyze_text("CrashLoopBackOff", enrich=True)
    assert result.enrichment is not None
    assert result.enrichment.provider == "fake"
    assert "an extra hypothesis" in result.enrichment.additional_causes
```

To assert graceful degradation, use the default `NullProvider` and check the low-severity warning:

```python
def test_enrichment_without_provider_is_safe():
    result = AnalysisEngine().analyze_text("CrashLoopBackOff", enrich=True)
    assert result.enrichment is None
    assert result.matched  # deterministic results still returned
```

## Testing with a custom knowledge base

Build a small `KnowledgeBase` so a test doesn't depend on packaged data:

```python
from devops_ai_toolkit import AnalysisEngine
from devops_ai_toolkit.knowledge.loader import KnowledgeBase

def test_custom_signature(tmp_path):
    (tmp_path / "custom.yaml").write_text(
        """
        - id: demo.boom
          technology: linux
          title: "Boom"
          summary: "A demo error."
          match: { any_of: ["BOOM"], weight: 0.9 }
          root_causes:
            - { title: "It went boom", description: "x", confidence: 0.8, category: demo }
        """
    )
    kb = KnowledgeBase.from_yaml_dir(str(tmp_path))
    engine = AnalysisEngine(knowledge_base=kb)
    assert engine.analyze_text("BOOM").signatures_matched == ["demo.boom"]
```

## Testing the REST API

Use FastAPI's `TestClient` (backed by `httpx`):

```python
from fastapi.testclient import TestClient
from devops_ai_toolkit.api.app import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_analyze_log():
    r = client.post("/analyze/log", json={"content": "OOMKilled exit code 137"})
    assert r.status_code == 200
    assert r.json()["matched"] is True
```

## Testing the CLI

Use Typer's runner:

```python
from typer.testing import CliRunner
from devops_ai_toolkit.cli.app import app

runner = CliRunner()

def test_explain():
    result = runner.invoke(app, ["explain", "CrashLoopBackOff"])
    assert result.exit_code == 0
```

## Settings in tests

Build `Settings` directly to avoid env coupling:

```python
from devops_ai_toolkit.utils.config import Settings

settings = Settings(provider="null", max_input_chars=1000)
```

`Settings.from_env({...})` also accepts an explicit env dict.

## What to cover when contributing

- A new **signature**: a test asserting it fires on a representative input and ranks sensibly.
- A new **provider**: tests for `available()` true/false and `complete()` parsing (mock HTTP).
- New **engine logic**: deterministic input/output assertions.
- Mark cross-interface tests with `@pytest.mark.integration`.

See [Contributing](contributing.md) and [Coding standards](coding-standards.md).
