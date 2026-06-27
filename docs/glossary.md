# Glossary

Terms used throughout the documentation.

### AnalysisEngine
The single façade that holds all business logic. The CLI, SDK, and REST API are thin adapters over
it. See [Architecture](architecture.md).

### AnalysisRequest
The structured input model for `engine.analyze()`: `content` plus optional `technology`,
`source_kind`, `filename`, `enrich`, and `max_root_causes`. See [SDK guide](sdk-guide.md).

### AnalysisResult
The canonical, interface-agnostic output of an analysis — summary, root causes, diagnostic
commands, fixes, references, warnings, best practices, prevention, optional enrichment, and
metadata. See [Output format](output-format.md).

### Adapter
A thin layer translating between the outside world and the engine. The CLI, SDK, and API are
interface adapters; AI providers are outbound adapters.

### AIProvider
The `Protocol` every LLM backend implements (`name`, `model`, `available()`, `complete()`). The
engine depends on this protocol, never a vendor SDK. See [AI providers](ai-providers.md).

### CompletionRequest
The data passed to a provider's `complete()`: `system`, `prompt`, `max_tokens`, `temperature`.

### Confidence / confidence band
A root cause's 0.0–1.0 likelihood. Bands bucket scores into `very_low`, `low`, `moderate`, `high`,
`very_high`. See [Output format](output-format.md#rootcause).

### DiagnosticCommand
A **read-only** command a human can run to confirm a hypothesis. `read_only` is always `true`; the
toolkit never executes it.

### Enrichment
Optional LLM-generated narrative and extra hypotheses layered on top of deterministic findings,
present only when `enrich=True` and a provider is available.

### ErrorCatalog
A view over the knowledge base used by `explain` and `list` to browse signatures.

### Evidence
The input line snippets that caused a signature to match — used to justify a finding.

### KnowledgeBase
The loaded collection of signatures the engine matches against. Packaged by default; can be
custom. See [Knowledge base](knowledge-base.md).

### NullProvider
The default offline provider. Always "unavailable", which keeps the toolkit deterministic and
network-free unless you configure a real provider.

### Read-only
The core guarantee: the toolkit reads text and emits guidance, and never executes commands or
mutates state. See [Security](security.md).

### RootCause
A ranked candidate explanation for the observed symptoms, with title, description, confidence,
category, and evidence.

### Signature
A declarative YAML rule: match patterns plus the root causes, commands, fixes, references, and
advice to emit when it fires. See [Knowledge base](knowledge-base.md).

### SignatureMatcher
The component that evaluates signatures (case-insensitive regex, `any_of`/`all_of`, weighting)
against an input and returns scored matches with evidence.

### SourceKind
The shape of the input: `log`, `yaml`, `terraform`, `compose`, `kubernetes_manifest`,
`command_output`, `error_string`, `unknown`.

### Technology
A supported platform the engine reasons about (e.g. `kubernetes`, `terraform`, `openstack`). See
[Supported technologies](supported-technologies.md).

### ValidationResult / ValidationIssue
The output of read-only manifest validation, and a single problem within it (severity, message,
optional line/path, hint).

### Warning
A caution surfaced to the operator (e.g. a fix that risks data loss), with a severity.
