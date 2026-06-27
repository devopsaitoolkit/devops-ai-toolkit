#!/usr/bin/env bash
#
# curl examples for the DevOps AI Toolkit REST API.
#
# Start the API first (in another terminal):
#   pip install -e '.[api]'
#   devops-ai serve --host 127.0.0.1 --port 8000
#
# Then run:  bash examples/curl_examples.sh
#
# Requires: curl. `jq` is optional (used only to pretty-print if present).

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Pretty-print JSON with jq when available, otherwise pass through raw.
pretty() {
  if command -v jq >/dev/null 2>&1; then jq .; else cat; fi
}

echo "### GET /health"
curl -fsS "${BASE_URL}/health" | pretty
echo

echo "### GET /version"
curl -fsS "${BASE_URL}/version" | pretty
echo

echo "### POST /analyze/log  (CrashLoopBackOff log)"
# Send the file contents as the JSON "content" field. --arg + jq builds valid JSON
# even when the log contains quotes/newlines.
jq -Rs '{content: .}' "${REPO_ROOT}/sample_logs/kubernetes_crashloopbackoff.log" \
  | curl -fsS -X POST "${BASE_URL}/analyze/log" \
      -H 'Content-Type: application/json' \
      --data @- \
  | pretty
echo

echo "### POST /analyze/log  (inline content, no file)"
curl -fsS -X POST "${BASE_URL}/analyze/log" \
  -H 'Content-Type: application/json' \
  -d '{"content": "ERROR: No valid host was found. There are not enough hosts available."}' \
  | pretty
echo

echo "### POST /explain  (explain a known error by name)"
curl -fsS -X POST "${BASE_URL}/explain" \
  -H 'Content-Type: application/json' \
  -d '{"error": "Error acquiring the state lock"}' \
  | pretty
echo

echo "### POST /validate  (validate a manifest, read-only)"
jq -Rs '{content: ., filename: "deployment_bad_practices.yaml"}' \
    "${REPO_ROOT}/sample_yaml/deployment_bad_practices.yaml" \
  | curl -fsS -X POST "${BASE_URL}/validate" \
      -H 'Content-Type: application/json' \
      --data @- \
  | pretty
echo
