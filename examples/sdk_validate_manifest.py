#!/usr/bin/env python3
"""SDK example: validate Kubernetes / YAML / Terraform manifests (read-only).

`validate_manifest` parses the document and reports issues (severity, message,
line, and a hint) plus best-practice suggestions. It never mutates the file.

Run it:

    pip install -e .
    python examples/sdk_validate_manifest.py
    python examples/sdk_validate_manifest.py sample_yaml/invalid_syntax.yaml
"""

from __future__ import annotations

import sys
from pathlib import Path

from devops_ai_toolkit import AnalysisEngine

REPO_ROOT = Path(__file__).resolve().parent.parent

# A few bundled manifests covering good, bad-practice, and broken-syntax cases.
DEFAULT_TARGETS = [
    REPO_ROOT / "sample_yaml" / "valid_deployment.yaml",
    REPO_ROOT / "sample_yaml" / "deployment_bad_practices.yaml",
    REPO_ROOT / "sample_yaml" / "invalid_syntax.yaml",
]


def validate_one(engine: AnalysisEngine, path: Path) -> bool:
    """Validate a single manifest and print its issues. Returns True if valid."""
    content = path.read_text(encoding="utf-8", errors="replace")

    # filename helps the engine pick the right validator (k8s vs terraform vs yaml).
    result = engine.validate_manifest(content, filename=path.name)

    status = "VALID" if result.valid else "INVALID"
    print(f"== {path.name} -> {status} ({result.technology}, {result.error_count} error(s)) ==")

    for issue in result.issues:
        location = f"L{issue.line}" if issue.line is not None else "-"
        path_hint = f" [{issue.path}]" if issue.path else ""
        print(f"  [{issue.severity}] {location}{path_hint}: {issue.message}")
        if issue.hint:
            print(f"        hint: {issue.hint}")

    for practice in result.best_practices:
        print(f"  best-practice: {practice}")

    print()
    return result.valid


def main() -> int:
    """Validate the CLI-provided file, or all bundled sample manifests."""
    targets = [Path(p) for p in sys.argv[1:]] or DEFAULT_TARGETS
    engine = AnalysisEngine()

    all_valid = True
    for target in targets:
        if not target.exists():
            print(f"File not found: {target}", file=sys.stderr)
            all_valid = False
            continue
        all_valid &= validate_one(engine, target)

    # Exit non-zero if anything failed validation (useful in CI).
    return 0 if all_valid else 1


if __name__ == "__main__":
    raise SystemExit(main())
