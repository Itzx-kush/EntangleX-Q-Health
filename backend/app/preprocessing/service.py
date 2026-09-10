from __future__ import annotations
import uuid
from datetime import datetime,timezone
import joblib,numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder,MinMaxScaler,OneHotEncoder,OrdinalEncoder,StandardScaler
from app.core.config import settings
from app.data.loader import load_dataframe_path
from app.data.repository import DatasetRepository
from app.preprocessing.errors import PreprocessingError
from app.preprocessing.feature_reduction import reduce_features
from app.preprocessing.outliers import OutlierPolicy
from app.preprocessing.repository import PreprocessingRepository
from app.preprocessing.resampling import apply_resampling
class PreprocessingService:
 def __init__(self,datasets=None,runs=None,upload_dir=None,artifact_dir=None):self.datasets=datasets or DatasetRepository();self.runs=runs or PreprocessingRepository();self.upload_dir=upload_dir or settings.upload_dir;self.artifact_dir=artifact_dir or settings.model_dir/'preprocessing';self.artifact_dir.mkdir(parents=True,exist_ok=True)
 def validate_config(self,c):return c.model_dump()
 def run(self,c):
  record=self.datasets.get(c.dataset_id)
  if not record:raise PreprocessingError('DATASET_NOT_FOUND','Dataset was not found.',c.dataset_id,404)
  target=record.get('target_column')
  if not target:raise PreprocessingError('TARGET_REQUIRED','Select and validate a binary target before preprocessing.')
  frame=load_dataframe_path(self.upload_dir/record['stored_filename']);input_rows=len(frame);duplicates=int(frame.duplicated().sum())
  if c.duplicate_mode=='remove':frame=frame.drop_duplicates().reset_index(drop=True)
  X=frame.drop(columns=[target]);y=frame[target];rows_after_duplicates=len(frame)
  try:X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=c.test_size,random_state=c.random_seed,stratify=y)
  except ValueError as exc:raise PreprocessingError('SPLIT_FAILED','Stratified train/test split failed.',str(exc)) from exc
  policy=OutlierPolicy(c.outlier_method,c.outlier_threshold).fit(X_train);removed=0
  if c.outlier_mode=='clip':X_train=policy.clip(X_train);X_test=policy.clip(X_test)
  elif c.outlier_mode=='remove':mask=policy.inlier_mask(X_train);removed=int((~mask).sum());X_train=X_train.loc[mask];y_train=y_train.loc[mask]
  numerical=[str(x) for x in X_train.select_dtypes(include='number').columns];categorical=[str(x) for x in X_train.columns if str(x) not in numerical];transformers=[]
  if numerical:transformers.append(('numerical',Pipeline([('imputer',SimpleImputer(strategy=c.numerical_missing)),('scaler',StandardScaler() if c.scaling=='standard' else MinMaxScaler())]),numerical))
  if categorical:transformers.append(('categorical',Pipeline([('imputer',SimpleImputer(strategy=c.categorical_missing)),('encoder',OneHotEncoder(handle_unknown='ignore',sparse_output=False) if c.categorical_encoding=='one_hot' else OrdinalEncoder(handle_unknown='use_encoded_value',unknown_value=-1))]),categorical))
  pipeline=ColumnTransformer(transformers=transformers,remainder='drop',verbose_feature_names_out=True);train_values=pipeline.fit_transform(X_train,y_train);test_values=pipeline.transform(X_test);labels=LabelEncoder().fit(y_train);train_labels=labels.transform(y_train);test_labels=labels.transform(y_test);transformed_names=[str(n) for n in pipeline.get_feature_names_out()]
  reduced=reduce_features(train_values,test_values,train_labels,transformed_names,c.feature_selection_method,c.feature_count,c.variance_threshold,c.reduction_method,c.pca_components,c.random_seed);sampled=apply_resampling(reduced.train,train_labels,c.resampling_method,c.random_seed,c.smote_k_neighbors);names=reduced.output_feature_names;run_id=str(uuid.uuid4());artifact=self.artifact_dir/f'{run_id}.joblib'
  bundle={'pipeline':pipeline,'outlier_policy':policy,'label_encoder':labels,'feature_selector':reduced.selector,'dimensionality_reducer':reduced.reducer,'configuration':c.model_dump(),'input_columns':[str(x) for x in X.columns],'output_feature_names':names,'training_features':sampled.features,'training_labels':sampled.labels,'test_features':reduced.test,'test_labels':test_labels,'fitted_on':'training_only'};joblib.dump(bundle,artifact)
  summary={'input_rows':input_rows,'rows_after_duplicates':rows_after_duplicates,'duplicates_removed':duplicates if c.duplicate_mode=='remove' else 0,'train_rows':len(X_train),'test_rows':len(X_test),'train_rows_before_resampling':sampled.rows_before,'train_rows_after_resampling':sampled.rows_after,'resampling_method':sampled.method,'resampling_rows_added':sampled.rows_added,'resampling_rows_removed':sampled.rows_removed,'outliers_removed_from_train':removed,'input_features':X.shape[1],'transformed_features':len(transformed_names),'selected_features':len(reduced.selected_feature_names),'output_features':len(names),'feature_selection_method':c.feature_selection_method,'reduction_method':c.reduction_method,'selected_feature_names':reduced.selected_feature_names,'explained_variance_ratio':reduced.explained_variance_ratio,'explained_variance_total':round(sum(reduced.explained_variance_ratio),8) if reduced.explained_variance_ratio else None,'numerical_features':numerical,'categorical_features':categorical,'output_feature_names':names,'train_class_distribution':self._counts(y_train),'train_class_distribution_before_resampling':sampled.distribution_before,'train_class_distribution_after_resampling':sampled.distribution_after,'test_class_distribution':self._counts(y_test),'fitted_on':'training_only'};r={'id':run_id,'dataset_id':c.dataset_id,'status':'completed','configuration':c.model_dump(),'summary':summary,'artifact_path':f'preprocessing/{run_id}.joblib','created_at':datetime.now(timezone.utc).isoformat()};self.runs.create(r);return self._response(r)
 def get(self,i):
  r=self.runs.get(i)
  if not r:raise PreprocessingError('PREPROCESSING_RUN_NOT_FOUND','Preprocessing run was not found.',i,404)
  return self._response(r)
 def list(self,dataset_id=None):return[self._response(r) for r in self.runs.list(dataset_id)]
 @staticmethod
 def _counts(v):return{str(k):int(n) for k,n in v.value_counts().items()}
 @staticmethod
 def _response(r):return{'id':r['id'],'dataset_id':r['dataset_id'],'status':r['status'],'configuration':r['configuration'],'artifact_path':r['artifact_path'],'created_at':r['created_at'],**r['summary']}
