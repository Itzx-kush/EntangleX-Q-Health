from __future__ import annotations
import uuid
from datetime import datetime,timezone
from pathlib import Path
import joblib,numpy as np,pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder,MinMaxScaler,OneHotEncoder,OrdinalEncoder,StandardScaler
from app.core.config import settings
from app.data.loader import load_dataframe_path
from app.data.repository import DatasetRepository
from app.preprocessing.errors import PreprocessingError
from app.preprocessing.outliers import OutlierPolicy
from app.preprocessing.repository import PreprocessingRepository
from app.preprocessing.resampling import apply_resampling
from app.preprocessing.schemas import PreprocessingConfig
class PreprocessingService:
 def __init__(self,datasets=None,runs=None,upload_dir=None,artifact_dir=None):self.datasets=datasets or DatasetRepository();self.runs=runs or PreprocessingRepository();self.upload_dir=upload_dir or settings.upload_dir;self.artifact_dir=artifact_dir or settings.model_dir/"preprocessing";self.artifact_dir.mkdir(parents=True,exist_ok=True)
 def validate_config(self,config):return config.model_dump()
 def run(self,config):
  record=self.datasets.get(config.dataset_id)
  if not record:raise PreprocessingError("DATASET_NOT_FOUND","Dataset was not found.",config.dataset_id,404)
  target=record.get("target_column")
  if not target:raise PreprocessingError("TARGET_REQUIRED","Select and validate a binary target before preprocessing.")
  path=self.upload_dir/record["stored_filename"]
  if not path.exists():raise PreprocessingError("DATASET_FILE_MISSING","The registered dataset file is unavailable.",str(path),404)
  frame=load_dataframe_path(path);input_rows=len(frame);duplicates=int(frame.duplicated().sum())
  if config.duplicate_mode=="remove":frame=frame.drop_duplicates().reset_index(drop=True)
  rows_after_duplicates=len(frame);X=frame.drop(columns=[target]);y=frame[target]
  if X.shape[1]==0:raise PreprocessingError("NO_FEATURES","Dataset has no feature columns after removing the target.")
  try:X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=config.test_size,random_state=config.random_seed,stratify=y)
  except ValueError as exc:raise PreprocessingError("SPLIT_FAILED","Stratified train/test split failed.",str(exc)) from exc
  policy=OutlierPolicy(config.outlier_method,config.outlier_threshold).fit(X_train);removed=0
  if config.outlier_mode=="clip":X_train=policy.clip(X_train);X_test=policy.clip(X_test)
  elif config.outlier_mode=="remove":
   mask=policy.inlier_mask(X_train);removed=int((~mask).sum());X_train=X_train.loc[mask];y_train=y_train.loc[mask]
   if y_train.nunique()!=2:raise PreprocessingError("OUTLIER_REMOVAL_INVALIDATED_TARGET","Outlier removal left fewer than two training classes.")
  numerical=[str(c) for c in X_train.select_dtypes(include="number").columns];categorical=[str(c) for c in X_train.columns if str(c) not in numerical];transformers=[]
  if numerical:transformers.append(("numerical",Pipeline([("imputer",SimpleImputer(strategy=config.numerical_missing)),("scaler",StandardScaler() if config.scaling=="standard" else MinMaxScaler())]),numerical))
  if categorical:transformers.append(("categorical",Pipeline([("imputer",SimpleImputer(strategy=config.categorical_missing)),("encoder",OneHotEncoder(handle_unknown="ignore",sparse_output=False) if config.categorical_encoding=="one_hot" else OrdinalEncoder(handle_unknown="use_encoded_value",unknown_value=-1))]),categorical))
  pipeline=ColumnTransformer(transformers=transformers,remainder="drop",verbose_feature_names_out=True)
  try:train_values=pipeline.fit_transform(X_train,y_train);test_values=pipeline.transform(X_test)
  except Exception as exc:raise PreprocessingError("PREPROCESSING_FAILED","Preprocessing could not be fitted or applied.",str(exc)) from exc
  if not np.isfinite(np.asarray(train_values,dtype=float)).all() or not np.isfinite(np.asarray(test_values,dtype=float)).all():raise PreprocessingError("NON_FINITE_OUTPUT","Preprocessing produced non-finite values.")
  labels=LabelEncoder().fit(y_train);train_labels=labels.transform(y_train)
  try:labels.transform(y_test)
  except ValueError as exc:raise PreprocessingError("UNSEEN_TEST_LABEL","Test split contains a target label absent from training.",str(exc)) from exc
  sampled=apply_resampling(train_values,train_labels,config.resampling_method,config.random_seed,config.smote_k_neighbors);names=[str(n) for n in pipeline.get_feature_names_out()];run_id=str(uuid.uuid4());artifact=self.artifact_dir/f"{run_id}.joblib"
  bundle={"pipeline":pipeline,"outlier_policy":policy,"label_encoder":labels,"resampling":{"method":sampled.method,"rows_before":sampled.rows_before,"rows_after":sampled.rows_after,"distribution_before":sampled.distribution_before,"distribution_after":sampled.distribution_after},"configuration":config.model_dump(),"input_columns":[str(c) for c in X.columns],"output_feature_names":names,"fitted_on":"training_only"};joblib.dump(bundle,artifact)
  summary={"input_rows":input_rows,"rows_after_duplicates":rows_after_duplicates,"duplicates_removed":duplicates if config.duplicate_mode=="remove" else 0,"train_rows":len(X_train),"test_rows":len(X_test),"train_rows_before_resampling":sampled.rows_before,"train_rows_after_resampling":sampled.rows_after,"resampling_method":sampled.method,"resampling_rows_added":sampled.rows_added,"resampling_rows_removed":sampled.rows_removed,"outliers_removed_from_train":removed,"input_features":X.shape[1],"output_features":len(names),"numerical_features":numerical,"categorical_features":categorical,"output_feature_names":names,"train_class_distribution":self._counts(y_train),"train_class_distribution_before_resampling":sampled.distribution_before,"train_class_distribution_after_resampling":sampled.distribution_after,"test_class_distribution":self._counts(y_test),"fitted_on":"training_only"};record={"id":run_id,"dataset_id":config.dataset_id,"status":"completed","configuration":config.model_dump(),"summary":summary,"artifact_path":f"preprocessing/{run_id}.joblib","created_at":datetime.now(timezone.utc).isoformat()}
  try:self.runs.create(record)
  except Exception:artifact.unlink(missing_ok=True);raise
  return self._response(record)
 def get(self,run_id):
  record=self.runs.get(run_id)
  if not record:raise PreprocessingError("PREPROCESSING_RUN_NOT_FOUND","Preprocessing run was not found.",run_id,404)
  return self._response(record)
 def list(self,dataset_id=None):return [self._response(r) for r in self.runs.list(dataset_id)]
 @staticmethod
 def _counts(values):return {str(k):int(v) for k,v in values.value_counts().items()}
 @staticmethod
 def _response(record):return {"id":record["id"],"dataset_id":record["dataset_id"],"status":record["status"],"configuration":record["configuration"],"artifact_path":record["artifact_path"],"created_at":record["created_at"],**record["summary"]}
