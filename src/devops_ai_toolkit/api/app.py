"""FastAPI application exposing the analysis engine over HTTP.

Every route delegates to a single shared :class:`AnalysisEngine` instance, so the
REST API has zero business logic of its own — it only marshals JSON. OpenAPI /
Swagger UI is generated automatically at ``/docs`` and ``/redoc``.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, FastAPI

from .._version import __version__
from ..analysis import AnalysisEngine
from ..models.analysis import (
    AnalysisRequest,
    AnalysisResult,
    ExplainResult,
    ValidationResult,
)
from .schemas import (
    AnalyzeBody,
    ExplainBody,
    HealthResponse,
    ValidateBody,
    VersionResponse,
)

app = FastAPI(
    title="DevOps AI Toolkit API",
    version=__version__,
    description=(
        "Read-only, AI-powered DevOps troubleshooting. Analyze logs, manifests and "
        "Terraform; explain errors; validate manifests. Powered by the same engine as "
        "the CLI and SDK. Docs and guides: https://devopsaitoolkit.com"
    ),
    contact={"name": "DevOps AI Toolkit", "url": "https://devopsaitoolkit.com"},
    license_info={"name": "MIT"},
)


@lru_cache(maxsize=1)
def get_engine() -> AnalysisEngine:
    """Provide a process-wide engine instance (cached)."""
    return AnalysisEngine()


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health(engine: AnalysisEngine = Depends(get_engine)) -> HealthResponse:
    """Liveness and readiness probe with knowledge-base and provider status."""
    return HealthResponse(
        signatures=len(engine.knowledge_base),
        provider=engine.provider.name,
        provider_available=engine.provider.available(),
    )


@app.get("/version", response_model=VersionResponse, tags=["meta"])
def version() -> VersionResponse:
    """Return the running version."""
    return VersionResponse(version=__version__)


@app.post("/analyze/log", response_model=AnalysisResult, tags=["analyze"])
def analyze_log(body: AnalyzeBody, engine: AnalysisEngine = Depends(get_engine)) -> AnalysisResult:
    """Analyze a log or command output."""
    return engine.analyze(AnalysisRequest(**body.model_dump()))


@app.post("/analyze/yaml", response_model=AnalysisResult, tags=["analyze"])
def analyze_yaml(body: AnalyzeBody, engine: AnalysisEngine = Depends(get_engine)) -> AnalysisResult:
    """Analyze a YAML / Kubernetes manifest."""
    payload = body.model_dump()
    payload.setdefault("source_kind", None)
    return engine.analyze(AnalysisRequest(**payload))


@app.post("/analyze/terraform", response_model=AnalysisResult, tags=["analyze"])
def analyze_terraform(
    body: AnalyzeBody, engine: AnalysisEngine = Depends(get_engine)
) -> AnalysisResult:
    """Analyze Terraform configuration or plan/apply output."""
    return engine.analyze_terraform(body.content, enrich=body.enrich)


@app.post("/explain", response_model=ExplainResult, tags=["explain"])
def explain(body: ExplainBody, engine: AnalysisEngine = Depends(get_engine)) -> ExplainResult:
    """Explain a known error from the knowledge base."""
    return engine.explain_error(body.error)


@app.post("/validate", response_model=ValidationResult, tags=["validate"])
def validate(body: ValidateBody, engine: AnalysisEngine = Depends(get_engine)) -> ValidationResult:
    """Validate a YAML / Kubernetes / Terraform document."""
    return engine.validate_manifest(
        body.content,
        technology=body.technology,
        source_kind=body.source_kind,
        filename=body.filename,
    )
