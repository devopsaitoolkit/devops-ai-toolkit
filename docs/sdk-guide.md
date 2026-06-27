# SDK guide

The Python SDK *is* the engine. Importing `AnalysisEngine` gives you the exact same logic the CLI
and REST API use. Everything is read-only and offline by default.

```python
from devops_ai_toolkit import AnalysisEngine

engine = AnalysisEngine()
result = engine.analyze_file("nova.log")
print(result.summary)
```

## The public API

`from devops_ai_toolkit import ...` exposes:

| Symbol             | Kind   | Purpose                                              |
|--------------------|--------|------------------------------------------------------|
| `AnalysisEngine`   | class  | The façade you call                                  |
| `AnalysisRequest`  | model  | Structured input for `engine.analyze()`              |
| `AnalysisResult`   | model  | The canonical output ([Output format](output-format.md)) |
| `ExplainResult`    | model  | Output of `explain_error()`                          |
| `ValidationResult` | model  | Output of `validate_manifest()`                      |
| `Technology`       | enum   | Technology hints (`Technology.KUBERNETES`, …)        |
| `SourceKind`       | enum   | Input-shape hints (`SourceKind.YAML`, …)             |
| `ErrorCatalog`     | class  | Browse/iterate the knowledge base                    |
| `__version__`      | str    | Installed version                                    |

## Constructing an engine

```python
engine = AnalysisEngine()  # packaged knowledge base, offline NullProvider, env settings
```

All collaborators are injectable (handy for tests and custom setups):

```python
from devops_ai_toolkit import AnalysisEngine

engine = AnalysisEngine(
    knowledge_base=my_kb,   # KnowledgeBase | None
    provider=my_provider,   # AIProvider   | None
    settings=my_settings,   # Settings     | None
)
```

See the [Testing guide](testing-guide.md) and [Plugin guide](plugin-guide.md) for how to build
custom knowledge bases and providers.

## Analysis methods

### `analyze_file(path, *, enrich=False)`

Reads a file from disk (the only filesystem read the engine performs) and analyzes it.

```python
result = engine.analyze_file("app.log")
result = engine.analyze_file("deploy.yaml", enrich=True)
```

### `analyze_text(content, *, technology=None, source_kind=None, filename=None, enrich=False)`

Analyze a raw string with optional hints.

```python
from devops_ai_toolkit import Technology

result = engine.analyze_text(
    "ImagePullBackOff: pull access denied",
    technology=Technology.KUBERNETES,
)
```

### `analyze_yaml(content, *, enrich=False)`

Hints the source kind as YAML.

```python
result = engine.analyze_yaml(open("deploy.yaml").read())
```

### `analyze_terraform(content, *, enrich=False)`

Hints both technology and source kind as Terraform.

```python
result = engine.analyze_terraform(open("main.tf").read())
```

### `analyze(request)`

The structured form behind the convenience methods. Use it when you want full control.

```python
from devops_ai_toolkit import AnalysisRequest, Technology, SourceKind

req = AnalysisRequest(
    content=open("app.log").read(),
    technology=Technology.KUBERNETES,
    source_kind=SourceKind.LOG,
    filename="app.log",
    enrich=False,
    max_root_causes=3,
)
result = engine.analyze(req)
```

## Explaining an error

```python
explained = engine.explain_error("CrashLoopBackOff")
print(explained.matched)   # True if a signature matched
print(explained.title)
print(explained.summary)
for cmd in explained.diagnostic_commands:
    print(cmd.command, "—", cmd.explanation)
```

## Validating a manifest

```python
validation = engine.validate_manifest(open("deploy.yaml").read(), filename="deploy.yaml")
print("valid:", validation.valid, "errors:", validation.error_count)
for issue in validation.issues:
    print(f"[{issue.severity}] {issue.message} ({issue.path})")
```

## Working with results

`AnalysisResult` is a Pydantic model, so you get typed attributes and easy serialization:

```python
result = engine.analyze_file("app.log")

print(result.confidence_percent)        # 0-100, strongest root cause
print(result.matched)                   # bool
print([rc.title for rc in result.root_causes])

# Serialize
import json
print(result.model_dump_json(indent=2))
data = result.model_dump()              # plain dict
```

Every field is documented in [Output format](output-format.md).

## Browsing the catalog

```python
from devops_ai_toolkit import ErrorCatalog, Technology

catalog = ErrorCatalog()
print(len(catalog), "signatures")
for entry in catalog.entries(Technology.KUBERNETES):
    print(entry.id, entry.title)
```

## Enrichment (optional)

```python
result = engine.analyze_file("app.log", enrich=True)
if result.enrichment:
    print(result.enrichment.provider, result.enrichment.model)
    print(result.enrichment.narrative)
    print(result.enrichment.additional_causes)
```

If no provider is configured, the call still succeeds and returns deterministic results, with a
low-severity warning noting enrichment was skipped. See [AI providers](ai-providers.md).

## See also

- [Examples](examples.md) — more end-to-end snippets
- [CLI guide](cli-guide.md) and [REST API guide](rest-api-guide.md) — same engine, other shells
- Subscribe for new patterns and guides: <https://devopsaitoolkit.com/newsletter>
