from fastapi import APIRouter,Depends
from app.ml.schemas import ModelRun,ModelRunList,ModelTrainingConfig
from app.ml.service import ModelTrainingService
router=APIRouter(prefix="/api/models",tags=["models"]);_service=None
def get_model_service():
 global _service
 if _service is None:_service=ModelTrainingService()
 return _service
@router.post("/train",response_model=ModelRun,status_code=201)
def train(payload:ModelTrainingConfig,service=Depends(get_model_service)):return service.train(payload)
@router.get("/runs",response_model=ModelRunList)
def list_runs(preprocessing_run_id:str|None=None,service=Depends(get_model_service)):
 items=service.list(preprocessing_run_id);return{"items":items,"total":len(items)}
@router.get("/runs/{run_id}",response_model=ModelRun)
def get_run(run_id:str,service=Depends(get_model_service)):return service.get(run_id)
