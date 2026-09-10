from fastapi import APIRouter,Depends
from app.ml.schemas import ModelRun,ModelRunList,ModelTrainingConfig
from app.ml.service import ModelTrainingService
router=APIRouter(prefix='/api/models',tags=['models']);_service=None
def get_model_service():
 global _service
 if _service is None:_service=ModelTrainingService()
 return _service
@router.post('/train',response_model=ModelRun,status_code=201)
def train(p:ModelTrainingConfig,s=Depends(get_model_service)):return s.train(p)
@router.get('/runs',response_model=ModelRunList)
def runs(preprocessing_run_id:str|None=None,s=Depends(get_model_service)):
 x=s.list(preprocessing_run_id);return{'items':x,'total':len(x)}
