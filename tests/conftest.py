"""Shared pytest fixtures for the DevOps AI Toolkit test suite.

Everything is offline and deterministic: the default engine resolves to the
``NullProvider`` because no provider env vars are set. Tests that need a working
provider inject a fake one rather than touching the network.
"""

from __future__ import annotations

import pytest

from devops_ai_toolkit.analysis import AnalysisEngine
from devops_ai_toolkit.knowledge.loader import load_default_knowledge_base
from devops_ai_toolkit.providers.base import CompletionRequest
from devops_ai_toolkit.utils.config import Settings


@pytest.fixture(scope="session")
def knowledge_base():
    """The packaged, validated knowledge base (cached)."""
    return load_default_knowledge_base()


@pytest.fixture
def offline_settings() -> Settings:
    """Settings with no provider configured and no API keys (pure offline)."""
    return Settings(provider="null")


@pytest.fixture
def engine(offline_settings) -> AnalysisEngine:
    """A deterministic, offline AnalysisEngine instance."""
    return AnalysisEngine(settings=offline_settings)


class FakeProvider:
    """A deterministic in-memory AI provider, never touches the network."""

    name = "fake"
    model = "fake-model-1"

    def __init__(
        self, response: str = "This is a fake narrative.\nCAUSE: Extra hypothesis one."
    ) -> None:
        self._response = response
        self.calls: list[CompletionRequest] = []

    def available(self) -> bool:
        return True

    def complete(self, request: CompletionRequest) -> str:
        self.calls.append(request)
        return self._response


class FailingProvider:
    """A provider that is available but raises on complete()."""

    name = "failing"
    model = "failing-model"

    def available(self) -> bool:
        return True

    def complete(self, request: CompletionRequest):
        raise RuntimeError("simulated provider/network failure")


@pytest.fixture
def fake_provider() -> FakeProvider:
    return FakeProvider()


@pytest.fixture
def failing_provider() -> FailingProvider:
    return FailingProvider()


# ------------------------------------------------------------------ #
# Sample inputs                                                       #
# ------------------------------------------------------------------ #

CRASHLOOP_LOG = """\
2024-05-01T12:00:00Z kubelet: pod default/nginx-7d8 has status CrashLoopBackOff
Back-off restarting failed container nginx in pod nginx-7d8
Last State: Terminated, Reason: Error, Exit Code: 1
"""

IMAGEPULL_LOG = """\
Failed to pull image "myregistry/app:v9": ImagePullBackOff
Warning  Failed  pull access denied for myregistry/app, repository does not exist
"""

OOMKILLED_LOG = """\
container app terminated: OOMKilled (exit code 137)
kernel: Out of memory: Killed process 1234 (java)
"""

TERRAFORM_STATE_LOCK_LOG = """\
Error: Error acquiring the state lock

Lock Info:
  ID:        abc-123
  Path:      terraform.tfstate
  Operation: OperationTypeApply
"""

BENIGN_TEXT = "Everything is fine. The application started successfully and is serving traffic.\n"


@pytest.fixture
def crashloop_log() -> str:
    return CRASHLOOP_LOG


@pytest.fixture
def imagepull_log() -> str:
    return IMAGEPULL_LOG


@pytest.fixture
def oomkilled_log() -> str:
    return OOMKILLED_LOG


@pytest.fixture
def terraform_state_lock_log() -> str:
    return TERRAFORM_STATE_LOCK_LOG


@pytest.fixture
def benign_text() -> str:
    return BENIGN_TEXT


@pytest.fixture
def valid_k8s_manifest() -> str:
    return """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  template:
    spec:
      containers:
        - name: web
          image: nginx:1.25.3
          resources:
            requests: { memory: "128Mi" }
            limits: { memory: "256Mi" }
          livenessProbe:
            httpGet: { path: /healthz, port: 8080 }
"""


@pytest.fixture
def bad_k8s_manifest() -> str:
    """Missing required fields plus all the best-practice smells."""
    return """\
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
        - name: web
          image: nginx:latest
"""


@pytest.fixture
def invalid_yaml() -> str:
    return "foo: bar\n  bad: : indentation:\n\t- tabmix\n"


@pytest.fixture
def valid_terraform() -> str:
    return """\
resource "aws_s3_bucket" "logs" {
  bucket = "my-logs"
}

provider "aws" {
  region = "us-east-1"
}
"""


@pytest.fixture
def unbalanced_terraform() -> str:
    return 'resource "aws_s3_bucket" "logs" {\n  bucket = "my-logs"\n'
