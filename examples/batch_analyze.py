#!/usr/bin/env python3
"""Batch-analyze a directory of logs and print a results table.

Walks a directory (default: sample_logs/), analyzes every file with the SDK, and
prints one row per file: detected technology, whether a signature matched, the
overall confidence, and the top root cause.

Run it:

    pip install -e .
    python examples/batch_analyze.py
    python examples/batch_analyze.py sample_openstack
"""

from __future__ import annotations

import sys
from pathlib import Path

from devops_ai_toolkit import AnalysisEngine

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIR = REPO_ROOT / "sample_logs"

# File extensions worth analyzing as text input.
TEXT_SUFFIXES = {".log", ".txt", ".yaml", ".yml", ".tf"}


def iter_input_files(directory: Path):
    """Yield analyzable files in a directory, sorted by name."""
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def main() -> int:
    """Analyze every file in the target directory and print a table."""
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DIR
    if not target_dir.is_dir():
        print(f"Not a directory: {target_dir}", file=sys.stderr)
        return 2

    engine = AnalysisEngine()
    files = list(iter_input_files(target_dir))
    if not files:
        print(f"No analyzable files in {target_dir}")
        return 1

    # Column layout for the table.
    header = f"{'FILE':<42} {'TECHNOLOGY':<14} {'MATCH':<6} {'CONF':>5}  TOP CAUSE"
    print(header)
    print("-" * len(header))

    matched_count = 0
    for path in files:
        result = engine.analyze_file(path)
        if result.matched:
            matched_count += 1
        top = result.root_causes[0].title if result.root_causes else "-"
        print(
            f"{path.name:<42} "
            f"{result.technology!s:<14} "
            f"{('yes' if result.matched else 'no'):<6} "
            f"{result.confidence_percent:>4}%  "
            f"{top}"
        )

    print("-" * len(header))
    print(f"{matched_count}/{len(files)} files matched a known signature.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
