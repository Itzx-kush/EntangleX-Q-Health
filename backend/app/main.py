from __future__ import annotations
import logging
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.datasets import router as dataset_router
from app.api.health import router as health_router
from app.api.quantum import router as quantum_router
from app.api.qml import router as qml_router
from app.api.evaluations import router as evaluation_router
from app.api.models import router as model_router
from app.api.preprocessing import router as preprocessing_router
from app.api.orchestration import router as orchestration_router
from app.api.experiments import router as experiment_router
from app.api.benchmarks import router as benchmark_router
from app.api.explainability import router as explainability_router
from app.api.predictions import router as prediction_router
from app.api.platform import router as platform_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.data.errors import DatasetError
from app.evaluation.errors import EvaluationError
from app.ml.errors import ModelTrainingError
from app.quantum.errors import QuantumRuntimeError
from app.preprocessing.errors import PreprocessingError
from app.orchestration.errors import OrchestrationError
from app.experiments.errors import ExperimentError
from app.benchmarking.errors import BenchmarkError
from app.explainability.errors import ExplainabilityError
from app.prediction.errors import PredictionError
from app.platform.service import PlatformGovernanceService

configure_logging()
logger = logging.getLogger(__name__)
platform_audit = PlatformGovernanceService()

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version, description="Research and decision-support platform for reproducible hybrid quantum-classical biomedical ML.")
    app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=False, allow_methods=["GET", "POST", "DELETE"], allow_headers=["*"])
    app.include_router(health_router)
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(dataset_router)
    app.include_router(preprocessing_router)
    app.include_router(model_router)
    app.include_router(evaluation_router)
    app.include_router(quantum_router)
    app.include_router(qml_router)
    app.include_router(orchestration_router)
    app.include_router(experiment_router)
    app.include_router(benchmark_router)
    app.include_router(explainability_router)
    app.include_router(prediction_router)
    app.include_router(platform_router)

    @app.middleware("http")
    async def request_audit(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        principal = request.headers.get("x-role", "anonymous")[:80]
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            try:
                platform_audit.audit(request.method, request.url.path, status_code, principal, request_id)
            except Exception:
                logger.exception("Audit persistence failed")
        response.headers["X-Request-ID"] = request_id
        return response

    @app.exception_handler(DatasetError)
    async def dataset_error(_: Request, exc: DatasetError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, "details": exc.details})
    @app.exception_handler(PreprocessingError)
    async def preprocessing_error(_: Request, exc: PreprocessingError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, "details": exc.details})
    @app.exception_handler(ModelTrainingError)
    async def model_error(_: Request, exc: ModelTrainingError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, "details": exc.details})
    @app.exception_handler(EvaluationError)
    async def evaluation_error(_: Request, exc: EvaluationError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, "details": exc.details})
    @app.exception_handler(QuantumRuntimeError)
    async def quantum_error(_: Request, exc: QuantumRuntimeError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, "details": exc.details})
    @app.exception_handler(OrchestrationError)
    async def orchestration_error(_: Request, exc: OrchestrationError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, "details": exc.details})
    @app.exception_handler(ExperimentError)
    async def experiment_error(_: Request, exc: ExperimentError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, "details": exc.details})
    @app.exception_handler(BenchmarkError)
    async def benchmark_error(_: Request, exc: BenchmarkError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, "details": exc.details})
    @app.exception_handler(ExplainabilityError)
    async def explainability_error(_: Request, exc: ExplainabilityError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, "details": exc.details})
    @app.exception_handler(PredictionError)
    async def prediction_error(_: Request, exc: PredictionError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "message": exc.message, "details": exc.details})
    @app.exception_handler(Exception)
    async def unhandled_error(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API error")
        return JSONResponse(status_code=500, content={"error": "INTERNAL_ERROR", "message": "The request could not be completed.", "details": None})
    return app

app = create_app()
