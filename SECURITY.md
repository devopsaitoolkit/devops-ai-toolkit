# Security Policy

## Supported versions

Security fixes are applied to the latest released minor version. Because the
project is pre-1.0, we support only the most recent release line.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a vulnerability

Please report security issues **privately**. Do not open a public GitHub issue.

- Preferred: open a private advisory via
  [GitHub Security Advisories](https://github.com/devopsaitoolkit/devops-ai-toolkit/security/advisories/new).
- Alternatively, email **hello@devopsaitoolkit.com** with details and, if
  possible, a minimal reproduction.

We aim to acknowledge reports within 3 business days and to provide a remediation
timeline after triage. Please give us a reasonable window to release a fix before
any public disclosure.

## Read-only design as a security property

devops-ai-toolkit is intentionally designed to be **read-only**, and this is a
core security property rather than a side effect:

- **It never executes commands.** The tool analyzes the text you provide (logs,
  YAML, Terraform plans, Kubernetes manifests, etc.). It does not run `apply`,
  `delete`, `restart`, or any other mutating action against your infrastructure.
  "Diagnostic commands" surfaced by the knowledge base are *suggestions for you*
  to run, and are themselves read-only.
- **It never mutates the system it runs on**, beyond writing its own output
  where you direct it.
- **It does not transmit analyzed content** anywhere by default. The offline,
  deterministic core runs entirely locally with no network access.

### When data leaves the machine

The only time analyzed content can leave your machine is when **you explicitly
enable an external AI provider** (Anthropic, OpenAI, Gemini, or a self-hosted
Ollama endpoint) for optional enrichment. In that case the content you submit is
sent to the provider you configured, subject to that provider's terms. If you
need a fully air-gapped guarantee, run the offline core only, or point
enrichment at a self-hosted Ollama instance.

Because of this design, the most likely classes of vulnerability are
input-handling issues (e.g., parsing untrusted input) and supply-chain issues in
dependencies — these are exactly the reports we prioritize.
