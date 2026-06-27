#!/usr/bin/env python3
"""SDK quickstart: analyze a sample log file and print a readable summary.

The toolkit is read-only: it inspects text and returns ranked root causes plus
read-only diagnostic commands. It never runs commands or touches infrastructure.

Run it:

    pip install -e .            # from the repo root (installs devops_ai_toolkit)
    python examples/sdk_quickstart.py
    python examples/sdk_quickstart.py sample_logs/openstack_nova_no_valid_host.log
"""

from __future__ import annotations

import sys
from pathlib import Path

# The single public entry point. One engine powers the CLI, SDK and REST API.
from devops_ai_toolkit import AnalysisEngine

# Resolve paths relative to the repo root so the script runs from anywhere.
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SAMPLE = REPO_ROOT / "sample_logs" / "kubernetes_crashloopbackoff.log"


def main() -> int:
    """Analyze a file path (CLI arg or the bundled default) and print findings."""
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SAMPLE
    if not target.exists():
        print(f"File not found: {target}", file=sys.stderr)
        return 2

    # Construct the engine. With no AI provider configured it runs fully offline
    # and deterministic against the packaged knowledge base.
    engine = AnalysisEngine()

    # analyze_file is the only filesystem read the engine performs. It detects the
    # technology and input shape from the content + filename automatically.
    result = engine.analyze_file(target)

    print(f"== Analysis of {target.name} ==")
    print(f"Technology : {result.technology}")
    print(f"Source kind: {result.source_kind}")
    print(f"Matched    : {result.matched} (overall confidence {result.confidence_percent}%)")
    print(f"Signatures : {', '.join(result.signatures_matched) or '(none)'}")
    print()
    print("Summary:")
    print(f"  {result.summary}")
    print()

    if not result.matched:
        print(
            "No known signature matched. Try another sample or `--enrich` with a "
            "configured AI provider."
        )
        return 1

    # root_causes are already ranked most-likely-first by the engine.
    print("Top root causes:")
    for i, cause in enumerate(result.root_causes[:3], start=1):
        print(f"  {i}. [{cause.confidence_percent:>3}%] {cause.title} (category: {cause.category})")
        print(f"       {cause.description}")
    print()

    # Read-only diagnostic commands a human can run to confirm a hypothesis.
    print("Read-only diagnostic commands:")
    for cmd in result.diagnostic_commands[:3]:
        print(f"  $ {cmd.command}")
        print(f"      -> {cmd.explanation}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
