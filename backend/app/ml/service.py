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
 def __init__(self,preprocessing=None,models=None,preprocessing_artifact_dir=None,model_dir=None):self.preprocessing=preprocessing or PreprocessingRepository();self.models=models or ModelRepository();self.preprocessing_artifact_dir=preprocessing_artifact_dir or settings.model_dir/"preprocessing";self.model_dir=model_dir or settings.model_dir/"classical";self.model_dir.mkdir(parents=True,exist_ok=True)
 def train(self,config):
  run=self.preprocessing.get(config.preprocessing_run_id)
  if not run:raise ModelTrainingError("PREPROCESSING_RUN_NOT_FOUND","Preprocessing run was not found.",config.preprocessing_run_id,404)
  path=self.preprocessing_artifact_dir/Path(run["artifact_path"]).name
  if not path.exists():raise ModelTrainingError("PREPROCESSING_ARTIFACT_MISSING","Preprocessing artifact is unavailable.",str(path),404)
  bundle=joblib.load(path);required={"training_features","training_labels","test_features","test_labels"}
  if not required.issubset(bundle):raise ModelTrainingError("PREPROCESSING_ARTIFACT_INCOMPATIBLE","Rerun preprocessing with Phase 6 before training a model.")
  X=np.asarray(bundle["training_features"],dtype=float);y=np.asarray(bundle["training_labels"])
  if X.ndim!=2 or len(X)!=len(y) or len(np.unique(y))!=2:raise ModelTrainingError("INVALID_TRAINING_MATRIX","Prepared training data is invalid for binary classification.")
  estimator=build_estimator(config);started=perf_counter()
  try:estimator.fit(X,y)
  except Exception as exc:raise ModelTrainingError("MODEL_TRAINING_FAILED","Classical model training failed.",str(exc)) from exc
  duration=round(perf_counter()-started,6);run_id=str(uuid.uuid4());artifact=self.model_dir/f"{run_id}.joblib";reference=f"classical/{run_id}.joblib"
  joblib.dump({"model":estimator,"model_type":config.model_type,"configuration":config.model_dump(),"preprocessing_run_id":config.preprocessing_run_id,"dataset_id":run["dataset_id"],"feature_names":bundle["output_feature_names"],"test_features":bundle["test_features"],"test_labels":bundle["test_labels"],"label_encoder":bundle["label_encoder"]},artifact)
  summary={"training_rows":len(X),"feature_count":X.shape[1],"class_distribution":{str(k):int(v) for k,v in Counter(y.tolist()).items()},"training_duration_seconds":duration};record={"id":run_id,"preprocessing_run_id":config.preprocessing_run_id,"dataset_id":run["dataset_id"],"status":"completed","model_type":config.model_type,"configuration":config.model_dump(),"summary":summary,"artifact_path":reference,"created_at":datetime.now(timezone.utc).isoformat()}
  try:self.models.create(record)
  except Exception:artifact.unlink(missing_ok=True);raise
  return self._response(record)
 def get(self,run_id):
  r=self.models.get(run_id)
  if not r:raise ModelTrainingError("MODEL_RUN_NOT_FOUND","Model run was not found.",run_id,404)
  return self._response(r)
 def list(self,preprocessing_run_id=None):return[self._response(r) for r in self.models.list(preprocessing_run_id)]
 @staticmethod
 def _response(r):return{"id":r["id"],"preprocessing_run_id":r["preprocessing_run_id"],"dataset_id":r["dataset_id"],"status":r["status"],"model_type":r["model_type"],"configuration":r["configuration"],"artifact_path":r["artifact_path"],"created_at":r["created_at"],**r["summary"]}
