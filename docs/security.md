# Security

Security is a first-class design constraint, not an afterthought. The two pillars are the
**read-only guarantee** and **careful handling of optional API keys**.

## Read-only guarantee

The toolkit **never executes commands, mutates files, or touches infrastructure.** It only reads
text and produces guidance. Concretely:

- The **engine** is documented and built as read-only. Its single filesystem read is opening a file
  you explicitly pass to `analyze_file()`.
- **Diagnostic commands are suggestions, not actions.** The `DiagnosticCommand.read_only` field is
  always `true`, and the toolkit only ever suggests non-mutating commands. It does not run them.
- **Suggested fixes are guidance, never auto-applied.** They're returned as text/snippets for a
  human to review and apply.
- **Validation is inspection only.** `validate` parses and checks a document; it never applies it.

This means it is safe to point the toolkit at production logs and manifests: the worst it can do is
read the bytes you hand it.

## Input handling

- Input is **truncated** to `DEVOPS_AI_MAX_CHARS` (default 200,000) before analysis, bounding
  memory and, when enrichment is on, the amount of text sent to a provider. See
  [Configuration](configuration.md).
- Knowledge-base regex patterns are validated at load time; malformed patterns fail fast rather
  than running unbounded.
- Files are read with `errors="replace"`, so malformed bytes can't crash the reader.

## API key handling

By default the toolkit makes **no network calls** — the offline `NullProvider` is active and no key
is read or needed. Keys come into play only when you opt into [AI enrichment](ai-providers.md):

- Keys are read from **environment variables** (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
  `GEMINI_API_KEY`, etc.), never from positional CLI arguments and never written to disk by the
  toolkit.
- A key is sent **only to its own provider's endpoint** over HTTPS (e.g. the Anthropic key goes
  only to the Anthropic Messages API). The OpenAI adapter honours `OPENAI_BASE_URL` if you must
  route through an approved gateway.
- Keys are **not** included in `AnalysisResult`, logs, or error messages. The result's
  `enrichment` block records only the provider name and model — never the key.
- Provider/network failures are caught: a bad or missing key degrades to deterministic-only output
  rather than leaking details.

### Keeping data on-prem

For sensitive environments, either:

- Run **fully offline** (the default) — no data leaves the host, or
- Point enrichment at a **local Ollama** server so prompts never reach a third party:

  ```bash
  export DEVOPS_AI_PROVIDER=ollama
  export OLLAMA_HOST=http://localhost:11434
  ```

## What enrichment sends

When `enrich=true` and a provider is available, the engine sends a prompt built from the
deterministic result plus a bounded slice of the raw input (a fraction of `max_input_chars`).
Be mindful that operational text can contain secrets; redact before enabling enrichment if your
logs are sensitive, or keep enrichment off / local.

## Deploying the REST API

- The API ships **no authentication**. If you expose it beyond `localhost`, place it behind your
  own auth, TLS termination, and network policy.
- The engine needs **no write access** to the host or cluster.
- The instance is process-wide and stateless aside from the cached, read-only knowledge base.

## Reporting a vulnerability

Please report security issues privately via the repository's security contact / advisories rather
than a public issue. See [Contributing](contributing.md) for project contacts.

## See also

- [AI providers](ai-providers.md) — adapter behaviour and failure modes
- [Configuration](configuration.md) — every key and limit
- A managed, hardened option: the
  [AI incident assistant](https://devopsaitoolkit.com/dashboard/incident-response)
