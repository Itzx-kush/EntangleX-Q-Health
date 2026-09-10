from fastapi import APIRouter, Depends
from app.preprocessing.schemas import PreprocessingConfig, PreprocessingRun, PreprocessingRunList
from app.preprocessing.service import PreprocessingService
router=APIRouter(prefix="/api/preprocessing",tags=["preprocessing"]);_service:PreprocessingService|None=None
def get_preprocessing_service()->PreprocessingService:
    global _service
    if _service is None:_service=PreprocessingService()
    return _service
@router.post("/configure")
def configure(payload:PreprocessingConfig,service:PreprocessingService=Depends(get_preprocessing_service)):return {"valid":True,"configuration":service.validate_config(payload)}
@router.post("/run",response_model=PreprocessingRun,status_code=201)
def run(payload:PreprocessingConfig,service:PreprocessingService=Depends(get_preprocessing_service)):return service.run(payload)
@router.get("/runs",response_model=PreprocessingRunList)
def list_runs(dataset_id:str|None=None,service:PreprocessingService=Depends(get_preprocessing_service)):
    items=service.list(dataset_id);return {"items":items,"total":len(items)}
@router.get("/runs/{run_id}",response_model=PreprocessingRun)
def get_run(run_id:str,service:PreprocessingService=Depends(get_preprocessing_service)):return service.get(run_id)
