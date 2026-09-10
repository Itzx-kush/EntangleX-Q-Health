from fastapi import APIRouter,Depends
from app.evaluation.schemas import EvaluationRequest,EvaluationRun,EvaluationRunList
from app.evaluation.service import EvaluationService
router=APIRouter(prefix='/api/evaluations',tags=['evaluations']);_service=None
def get_evaluation_service():
 global _service
 if _service is None:_service=EvaluationService()
 return _service
@router.post('/run',response_model=EvaluationRun,status_code=201)
def run(p:EvaluationRequest,s=Depends(get_evaluation_service)):return s.run(p)
@router.get('/runs',response_model=EvaluationRunList)
def runs(model_run_id:str|None=None,s=Depends(get_evaluation_service)):
 x=s.list(model_run_id);return{'items':x,'total':len(x)}
@router.get('/runs/{run_id}',response_model=EvaluationRun)
def get_run(run_id:str,s=Depends(get_evaluation_service)):return s.get(run_id)
