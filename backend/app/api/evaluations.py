from fastapi import APIRouter,Depends
from app.evaluation.schemas import EvaluationRequest,EvaluationRun,EvaluationRunList
from app.evaluation.service import EvaluationService
router=APIRouter(prefix='/api/evaluations',tags=['evaluations']);_service=None
def get_evaluation_service():
 global _service
 if _service is None:_service=EvaluationService()
 return _service
@router.post('/run',response_model=EvaluationRun,status_code=201)
def run(payload:EvaluationRequest,service=Depends(get_evaluation_service)):return service.run(payload)
@router.get('/runs',response_model=EvaluationRunList)
def list_runs(model_run_id:str|None=None,service=Depends(get_evaluation_service)):
 items=service.list(model_run_id);return{'items':items,'total':len(items)}
@router.get('/runs/{run_id}',response_model=EvaluationRun)
def get_run(run_id:str,service=Depends(get_evaluation_service)):return service.get(run_id)
