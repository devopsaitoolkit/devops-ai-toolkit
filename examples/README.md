# Examples

Runnable examples for the **DevOps AI Toolkit** — a read-only, AI-powered
troubleshooting tool. It inspects logs, manifests, Terraform and command output
and returns ranked root causes plus read-only diagnostic commands. It never
executes commands or mutates infrastructure.

The same `AnalysisEngine` backs the CLI (`devops-ai`), the Python SDK
(`from devops_ai_toolkit import AnalysisEngine`) and the REST API
(`devops-ai serve`), so behaviour is identical across all three.

## Setup

```bash
# From the repo root
pip install -e .          # SDK + CLI
pip install -e '.[api]'   # also installs the REST API (FastAPI + uvicorn)
```

## Sample data

These examples read from the bundled sample directories at the repo root:

| Directory          | Contents                                                        |
| ------------------ | --------------------------------------------------------------- |
| `sample_logs/`     | Multi-line logs (Kubernetes, Docker, OpenStack, Linux, systemd, PostgreSQL, nginx, Prometheus, GitLab CI, RabbitMQ) |
| `sample_yaml/`     | Kubernetes manifests: good, bad-practice, broken-syntax, Service |
| `sample_terraform/`| `terraform apply` error output and `.tf` files                  |
| `sample_openstack/`| Nova / Neutron / Cinder CLI + log output                        |
| `sample_kubernetes/`| `kubectl describe` / status / events output                    |

Each sample contains the actual error strings the knowledge base matches, so
analyzing it produces a real, ranked result.

## SDK examples (Python)

| File                                       | What it shows                                          |
| ------------------------------------------ | ------------------------------------------------------ |
| [`sdk_quickstart.py`](sdk_quickstart.py)   | Analyze one file; print summary + top root causes      |
| [`sdk_validate_manifest.py`](sdk_validate_manifest.py) | Validate YAML/K8s/Terraform manifests (read-only) |
| [`batch_analyze.py`](batch_analyze.py)     | Analyze a whole directory; print a results table       |

```bash
python examples/sdk_quickstart.py
python examples/sdk_quickstart.py sample_logs/openstack_nova_no_valid_host.log
python examples/sdk_validate_manifest.py
python examples/batch_analyze.py sample_logs
```

## REST API examples

Start the server in one terminal:

```bash
devops-ai serve --host 127.0.0.1 --port 8000
# interactive docs at http://localhost:8000/docs
```

Then, in another terminal:

| File                                   | What it shows                                              |
| -------------------------------------- | --------------------------------------------------------- |
| [`api_client.py`](api_client.py)       | Python `requests` client hitting every endpoint           |
| [`curl_examples.sh`](curl_examples.sh) | `curl` calls against `/health`, `/analyze/log`, `/explain`, `/validate` |

```bash
pip install requests
python examples/api_client.py
bash examples/curl_examples.sh
```

## CLI quick reference

The examples mirror what the CLI does:

```bash
devops-ai analyze sample_logs/kubernetes_crashloopbackoff.log
devops-ai analyze sample_terraform/state_lock_error.txt --json
devops-ai explain "CrashLoopBackOff"
devops-ai validate sample_yaml/deployment_bad_practices.yaml
cat sample_logs/nginx_502_bad_gateway.log | devops-ai analyze -
devops-ai list --tech kubernetes
```
