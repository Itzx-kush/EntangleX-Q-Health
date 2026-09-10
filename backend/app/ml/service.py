from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from time import perf_counter
import uuid,joblib,numpy as np
from app.core.config import settings
from app.ml.errors import ModelTrainingError
from app.ml.factory import build_estimator
from app.ml.repository import ModelRepository
from app.preprocessing.repository import PreprocessingRepository
class ModelTrainingService:
 def __init__(self):self.preprocessing=PreprocessingRepository();self.models=ModelRepository();self.model_dir=settings.model_dir/'classical';self.model_dir.mkdir(parents=True,exist_ok=True)
 def train(self,c):
  r=self.preprocessing.get(c.preprocessing_run_id)
  if not r:raise ModelTrainingError('PREPROCESSING_RUN_NOT_FOUND','Preprocessing run was not found.',status_code=404)
  b=joblib.load(settings.model_dir/'preprocessing'/Path(r['artifact_path']).name)
  if 'training_features' not in b:raise ModelTrainingError('PREPROCESSING_ARTIFACT_INCOMPATIBLE','Rerun preprocessing with Phase 6.')
  X=np.asarray(b['training_features']);y=np.asarray(b['training_labels']);m=build_estimator(c);t=perf_counter();m.fit(X,y);duration=round(perf_counter()-t,6);i=str(uuid.uuid4());path=self.model_dir/f'{i}.joblib';joblib.dump({'model':m,'test_features':b['test_features'],'test_labels':b['test_labels'],'label_encoder':b['label_encoder'],'preprocessing_run_id':c.preprocessing_run_id},path);s={'training_rows':len(X),'feature_count':X.shape[1],'class_distribution':{str(k):int(v) for k,v in Counter(y.tolist()).items()},'training_duration_seconds':duration};record={'id':i,'preprocessing_run_id':c.preprocessing_run_id,'dataset_id':r['dataset_id'],'status':'completed','model_type':c.model_type,'configuration':c.model_dump(),'summary':s,'artifact_path':f'classical/{i}.joblib','created_at':datetime.now(timezone.utc).isoformat()};self.models.create(record);return self._response(record)
 def get(self,i):return self._response(self.models.get(i))
 def list(self,p=None):return[self._response(r) for r in self.models.list(p)]
 @staticmethod
 def _response(r):return{'id':r['id'],'preprocessing_run_id':r['preprocessing_run_id'],'dataset_id':r['dataset_id'],'status':r['status'],'model_type':r['model_type'],'configuration':r['configuration'],'artifact_path':r['artifact_path'],'created_at':r['created_at'],**r['summary']}
