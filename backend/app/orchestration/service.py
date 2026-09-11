from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
import uuid
from app.biomedical.adapters import ADAPTERS
from app.orchestration.errors import OrchestrationError
from app.orchestration.repository import TrainingJobRepository
from app.orchestration.schemas import BiomedicalValidationRequest, TrainingJobRequest
from app.ml.schemas import ModelTrainingConfig
from app.ml.service import ModelTrainingService
from app.quantum.qml_schemas import VQCRequest, QSVMRequest, QNNRequest
from app.quantum.vqc import VQCService
from app.quantum.qsvm import QSVMService
from app.quantum.qnn import QNNService

class TrainingOrchestrationService:
    def __init__(self, repository=None, classical=None, vqc=None, qsvm=None, qnn=None):
        self.jobs = repository or TrainingJobRepository()
        self.classical = classical or ModelTrainingService()
        self.vqc = vqc or VQCService()
        self.qsvm = qsvm or QSVMService()
        self.qnn = qnn or QNNService()

    def capabilities(self) -> list[dict[str, Any]]:
        return [{"modality": key, **value} for key, value in ADAPTERS.items()]

    def validate_modality(self, request: BiomedicalValidationRequest):
        from app.biomedical.adapters import validate_modality
        return validate_modality(request)

    def create(self, request: TrainingJobRequest):
        self._validate_lineage(request)
        now = datetime.now(timezone.utc).isoformat()
        job_id = str(uuid.uuid4())
        config = {"model_type": request.model_type, "modality": request.modality, "seed": request.seed, **request.model_parameters}
        record = {"id": job_id, "model_type": request.model_type, "modality": request.modality, "dataset_id": request.dataset_id,
                  "preprocessing_run_id": request.preprocessing_run_id, "encoding_run_id": request.encoding_run_id,
                  "status": "queued", "progress": 0, "configuration": config, "result": None, "error": None,
                  "cancel_requested": False, "parent_job_id": request.parent_job_id, "created_at": now, "started_at": None, "finished_at": None}
        self.jobs.create(record)
        return self.get(job_id)

    def run(self, job_id: str):
        record = self.jobs.get(job_id)
        if not record: raise OrchestrationError("JOB_NOT_FOUND", "Training job was not found.", job_id, 404)
        if record["status"] in {"completed", "failed", "cancelled"}: return self.get(job_id)
        if record["cancel_requested"]:
            self.jobs.update(job_id, status="cancelled", progress=0, finished_at=datetime.now(timezone.utc).isoformat()); return self.get(job_id)
        self.jobs.update(job_id, status="running", progress=10, started_at=datetime.now(timezone.utc).isoformat())
        try:
            config = record["configuration"]
            if record["model_type"] in {"logistic_regression", "svm", "random_forest"}:
                fields = {k:v for k,v in config.items() if k in ModelTrainingConfig.model_fields and k not in {"preprocessing_run_id", "model_type"}}
                result = self.classical.train(ModelTrainingConfig(preprocessing_run_id=record["preprocessing_run_id"], model_type=record["model_type"], **fields))
            else:
                self.jobs.update(job_id, progress=20)
                if record["model_type"] == "vqc": cls = VQCRequest; service = self.vqc
                elif record["model_type"] == "qsvm": cls = QSVMRequest; service = self.qsvm
                else: cls = QNNRequest; service = self.qnn
                fields = {k:v for k,v in config.items() if k in cls.model_fields and k != "encoding_run_id"}
                result = service.train(cls(encoding_run_id=record["encoding_run_id"], **fields))
            payload = result.model_dump(mode="json") if hasattr(result, "model_dump") else result
            self.jobs.update(job_id, status="completed", progress=100, result=payload, finished_at=datetime.now(timezone.utc).isoformat())
        except Exception as exc:
            self.jobs.update(job_id, status="failed", progress=100, error={"code": getattr(exc, "code", "TRAINING_FAILED"), "message": str(exc), "details": getattr(exc, "details", None)}, finished_at=datetime.now(timezone.utc).isoformat())
        return self.get(job_id)

    def cancel(self, job_id: str):
        record = self.jobs.get(job_id)
        if not record: raise OrchestrationError("JOB_NOT_FOUND", "Training job was not found.", job_id, 404)
        if record["status"] in {"completed", "failed", "cancelled"}: return self.get(job_id)
        self.jobs.update(job_id, cancel_requested=True, status="cancel_requested")
        return self.get(job_id)

    def get(self, job_id: str):
        record = self.jobs.get(job_id)
        if not record: raise OrchestrationError("JOB_NOT_FOUND", "Training job was not found.", job_id, 404)
        return record

    def list(self, dataset_id=None): return self.jobs.list(dataset_id)

    def rerun(self, job_id: str):
        original = self.jobs.get(job_id)
        if not original: raise OrchestrationError("JOB_NOT_FOUND", "Training job was not found.", job_id, 404)
        parameters = {k:v for k,v in original["configuration"].items() if k not in {"model_type", "modality"}}
        request = TrainingJobRequest(model_type=original["model_type"], modality=original["modality"], dataset_id=original["dataset_id"], preprocessing_run_id=original["preprocessing_run_id"], encoding_run_id=original["encoding_run_id"], model_parameters=parameters, seed=int(original["configuration"].get("seed", 42)), parent_job_id=job_id)
        return self.create(request)

    def _validate_lineage(self, request):
        if request.model_type in {"logistic_regression", "svm", "random_forest"} and not request.preprocessing_run_id:
            raise OrchestrationError("PREPROCESSING_LINEAGE_REQUIRED", "Classical jobs require a preprocessing_run_id.")
        if request.model_type in {"vqc", "qsvm", "qnn"} and not request.encoding_run_id:
            raise OrchestrationError("ENCODING_LINEAGE_REQUIRED", "Quantum jobs require an encoding_run_id.")
