from fastapi import APIRouter, Depends
from app.orchestration.errors import OrchestrationError
from app.orchestration.schemas import BiomedicalValidationRequest, BiomedicalValidationResult, TrainingJobRequest, TrainingJobResponse, TrainingJobList
from app.orchestration.service import TrainingOrchestrationService

router = APIRouter(prefix="/api/orchestration", tags=["training-orchestration"])
_service = None

def get_service():
    global _service
    if _service is None: _service = TrainingOrchestrationService()
    return _service

@router.get("/capabilities")
def capabilities(service=Depends(get_service)): return {"modalities": service.capabilities(), "models": ["logistic_regression", "svm", "random_forest", "vqc", "qsvm", "qnn"]}

@router.post("/validate", response_model=BiomedicalValidationResult)
def validate(payload: BiomedicalValidationRequest, service=Depends(get_service)): return service.validate_modality(payload)

@router.post("/jobs", response_model=TrainingJobResponse, status_code=201)
def create_job(payload: TrainingJobRequest, service=Depends(get_service)): return service.create(payload)

@router.post("/jobs/{job_id}/run", response_model=TrainingJobResponse)
def run_job(job_id: str, service=Depends(get_service)): return service.run(job_id)

@router.post("/jobs/{job_id}/cancel", response_model=TrainingJobResponse)
def cancel_job(job_id: str, service=Depends(get_service)): return service.cancel(job_id)

@router.post("/jobs/{job_id}/rerun", response_model=TrainingJobResponse, status_code=201)
def rerun_job(job_id: str, service=Depends(get_service)): return service.rerun(job_id)

@router.get("/jobs", response_model=TrainingJobList)
def list_jobs(dataset_id: str | None = None, service=Depends(get_service)):
    items = service.list(dataset_id); return {"items": items, "total": len(items)}

@router.get("/jobs/{job_id}", response_model=TrainingJobResponse)
def get_job(job_id: str, service=Depends(get_service)): return service.get(job_id)
