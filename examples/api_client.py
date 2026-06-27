#!/usr/bin/env python3
"""REST API client example using `requests`.

Start the API first (in another terminal):

    pip install -e '.[api]'
    devops-ai serve --host 127.0.0.1 --port 8000

Then run this script:

    pip install requests
    python examples/api_client.py

It exercises /health, /version, /analyze/log, /analyze/yaml, /analyze/terraform,
/explain and /validate. Interactive OpenAPI docs live at http://localhost:8000/docs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

BASE_URL = "http://localhost:8000"
REPO_ROOT = Path(__file__).resolve().parent.parent
TIMEOUT = 30


def _read(rel_path: str) -> str:
    """Read a bundled sample file as text."""
    return (REPO_ROOT / rel_path).read_text(encoding="utf-8", errors="replace")


def get_health() -> dict:
    """GET /health — knowledge-base size and provider status."""
    resp = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_version() -> dict:
    """GET /version — running toolkit version."""
    resp = requests.get(f"{BASE_URL}/version", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def analyze_log(content: str) -> dict:
    """POST /analyze/log — analyze a log or command output."""
    resp = requests.post(
        f"{BASE_URL}/analyze/log",
        json={"content": content},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def analyze_yaml(content: str) -> dict:
    """POST /analyze/yaml — analyze a YAML / Kubernetes manifest."""
    resp = requests.post(
        f"{BASE_URL}/analyze/yaml",
        json={"content": content},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def analyze_terraform(content: str) -> dict:
    """POST /analyze/terraform — analyze Terraform config or plan/apply output."""
    resp = requests.post(
        f"{BASE_URL}/analyze/terraform",
        json={"content": content},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def explain(error: str) -> dict:
    """POST /explain — explain a known error by name or message."""
    resp = requests.post(
        f"{BASE_URL}/explain",
        json={"error": error},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def validate(content: str, filename: str) -> dict:
    """POST /validate — validate a manifest (read-only)."""
    resp = requests.post(
        f"{BASE_URL}/validate",
        json={"content": content, "filename": filename},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def _print_top_cause(result: dict) -> None:
    """Print a one-line summary of an analysis response."""
    causes = result.get("root_causes", [])
    if causes:
        top = causes[0]
        print(f"    top cause [{top['confidence_percent']}%]: {top['title']}")
    else:
        print("    (no signature matched)")


def main() -> int:
    """Call each endpoint against the bundled sample data and print results."""
    try:
        health = get_health()
    except requests.exceptions.ConnectionError:
        print("Could not reach the API. Start it with: devops-ai serve", file=sys.stderr)
        return 1

    print(
        f"GET  /health   -> signatures={health['signatures']} "
        f"provider={health['provider']} available={health['provider_available']}"
    )
    print(f"GET  /version  -> {get_version()['version']}")
    print()

    log_result = analyze_log(_read("sample_logs/openstack_nova_no_valid_host.log"))
    print(f"POST /analyze/log -> {log_result['technology']} ({log_result['confidence_percent']}%)")
    _print_top_cause(log_result)

    yaml_result = analyze_yaml(_read("sample_yaml/deployment_bad_practices.yaml"))
    print(f"POST /analyze/yaml -> {yaml_result['technology']}")
    _print_top_cause(yaml_result)

    tf_result = analyze_terraform(_read("sample_terraform/state_lock_error.txt"))
    print(f"POST /analyze/terraform -> {tf_result['technology']}")
    _print_top_cause(tf_result)

    explained = explain("CrashLoopBackOff")
    print(f"POST /explain -> matched={explained['matched']} title={explained['title']!r}")

    validated = validate(_read("sample_yaml/invalid_syntax.yaml"), "invalid_syntax.yaml")
    print(f"POST /validate -> valid={validated['valid']} errors={validated['error_count']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
