# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-27

Initial public release.

### Added

- **Shared `AnalysisEngine`** powering every interface from a single
  deterministic core, so the CLI, SDK, and REST API return identical results.
- **Three interfaces on one engine:**
  - **CLI** (`devops-ai`) for terminal-driven troubleshooting.
  - **SDK** for embedding analysis into your own Python tools.
  - **REST API** (FastAPI) for service-to-service integration.
- **Knowledge base of 80+ error signatures across 19 technologies**, covering
  logs, YAML, Terraform, Kubernetes, Docker, OpenStack, and more.
- **Offline-first, deterministic core** that runs entirely locally with no
  network access and no command execution (read-only by design).
- **Optional AI enrichment** via pluggable providers — Anthropic, OpenAI,
  Gemini, and self-hosted Ollama — enabled only when the user explicitly
  configures one.

[Unreleased]: https://github.com/devopsaitoolkit/devops-ai-toolkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/devopsaitoolkit/devops-ai-toolkit/releases/tag/v0.1.0
