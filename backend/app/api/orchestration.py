from fastapi import APIRouter, Depends
from app.orchestration.schemas import BiomedicalValidationRequest, BiomedicalValidationResult, TrainingJobRequest, TrainingJobResponse, TrainingJobList
from app.orchestration.service import TrainingOrchestrationService
from app.controlled_experiments.schemas import ControlledExperimentRequest
from app.controlled_experiments.service import ControlledExperimentService

router = APIRouter(prefix="/api/orchestration", tags=["training-orchestration"])
_service = None
_controlled = None

def get_service():
    global _service
    if _service is None: _service = TrainingOrchestrationService()
    return _service

def get_controlled_service():
    global _controlled
    if _controlled is None: _controlled = ControlledExperimentService()
    return _controlled

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

@router.post("/controlled-experiments", status_code=202)
def create_controlled_experiment(payload: ControlledExperimentRequest, service=Depends(get_controlled_service)): return service.create(payload)
@router.get("/controlled-experiments")
def list_controlled_experiments(service=Depends(get_controlled_service)): return {"items":service.list(),"total":len(service.list())}
@router.get("/controlled-experiments/{experiment_id}")
def get_controlled_experiment(experiment_id: str, service=Depends(get_controlled_service)): return service.get(experiment_id)
@router.post("/controlled-experiments/{experiment_id}/cancel")
def cancel_controlled_experiment(experiment_id: str, service=Depends(get_controlled_service)): return service.cancel(experiment_id)
@router.post("/controlled-experiments/{experiment_id}/rerun", status_code=202)
def rerun_controlled_experiment(experiment_id: str, service=Depends(get_controlled_service)): return service.rerun(experiment_id)
@router.get("/runtime-diagnostics")
def runtime_diagnostics(service=Depends(get_controlled_service)): return service.diagnostics()
