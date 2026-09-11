from __future__ import annotations
import hashlib, uuid
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, OneHotEncoder, OrdinalEncoder, StandardScaler
from app.core.config import settings
from app.data.loader import load_dataframe_path
from app.data.repository import DatasetRepository
from app.preprocessing.errors import PreprocessingError
from app.preprocessing.feature_reduction import reduce_features
from app.preprocessing.outliers import OutlierPolicy
from app.preprocessing.repository import PreprocessingRepository
from app.preprocessing.resampling import apply_resampling
from app.preprocessing.schemas import PreprocessingConfig

class PreprocessingService:
    def __init__(self,datasets:DatasetRepository|None=None,runs:PreprocessingRepository|None=None,upload_dir:Path|None=None,artifact_dir:Path|None=None)->None:
        self.datasets=datasets or DatasetRepository();self.runs=runs or PreprocessingRepository();self.upload_dir=upload_dir or settings.upload_dir;self.artifact_dir=artifact_dir or settings.model_dir/"preprocessing";self.artifact_dir.mkdir(parents=True,exist_ok=True)
    def validate_config(self,config:PreprocessingConfig)->dict:return config.model_dump()
    def run(self,config:PreprocessingConfig)->dict:
        record=self.datasets.get(config.dataset_id)
        if not record:raise PreprocessingError("DATASET_NOT_FOUND","Dataset was not found.",config.dataset_id,404)
        target=record.get("target_column")
        if not target:raise PreprocessingError("TARGET_REQUIRED","Select and validate a target before preprocessing.")
        target_metadata=record.get("target") or {}
        selected_task=target_metadata.get("task_type","classification")
        if selected_task!=config.task_type:raise PreprocessingError("TASK_TYPE_MISMATCH","Preprocessing task type must match the validated dataset target.",f"Target: {selected_task}; requested: {config.task_type}.")
        path=self.upload_dir/record["stored_filename"]
        if not path.exists():raise PreprocessingError("DATASET_FILE_MISSING","The registered dataset file is unavailable.",str(path),404)
        frame=load_dataframe_path(path);input_rows=len(frame);duplicates=int(frame.duplicated().sum())
        if config.duplicate_mode=="remove":frame=frame.drop_duplicates().reset_index(drop=True)
        rows_after_duplicates=len(frame)
        X=frame.drop(columns=[target]);y=frame[target]
        if X.shape[1]==0:raise PreprocessingError("NO_FEATURES","Dataset has no feature columns after removing the target.")
        if config.task_type=="regression":y=pd.to_numeric(y,errors="raise").astype(float)
        try:X_train,X_test,y_train,y_test=train_test_split(X,y,test_size=config.test_size,random_state=config.random_seed,stratify=y if config.task_type=="classification" else None)
        except ValueError as exc:raise PreprocessingError("SPLIT_FAILED","Train/test split failed.",str(exc)) from exc
        policy=OutlierPolicy(config.outlier_method,config.outlier_threshold).fit(X_train)
        removed=0
        if config.outlier_mode=="clip":X_train=policy.clip(X_train);X_test=policy.clip(X_test)
        elif config.outlier_mode=="remove":
            mask=policy.inlier_mask(X_train);removed=int((~mask).sum());X_train=X_train.loc[mask];y_train=y_train.loc[mask]
            if config.task_type=="classification" and y_train.nunique()!=2:raise PreprocessingError("OUTLIER_REMOVAL_INVALIDATED_TARGET","Outlier removal left fewer than two training classes.")
            if config.task_type=="regression" and len(y_train)<4:raise PreprocessingError("OUTLIER_REMOVAL_INVALIDATED_TARGET","Outlier removal left too few regression training rows.")
        numerical=[str(column) for column in X_train.select_dtypes(include="number").columns]
        categorical=[str(column) for column in X_train.columns if str(column) not in numerical]
        transformers=[]
        if numerical:
            scaler=StandardScaler() if config.scaling=="standard" else MinMaxScaler(feature_range=(0.0,1.0))
            transformers.append(("numerical",Pipeline([("imputer",SimpleImputer(strategy=config.numerical_missing)),("scaler",scaler)]),numerical))
        if categorical:
            encoder=OneHotEncoder(handle_unknown="ignore",sparse_output=False) if config.categorical_encoding=="one_hot" else OrdinalEncoder(handle_unknown="use_encoded_value",unknown_value=-1)
            transformers.append(("categorical",Pipeline([("imputer",SimpleImputer(strategy=config.categorical_missing)),("encoder",encoder)]),categorical))
        pipeline=ColumnTransformer(transformers=transformers,remainder="drop",verbose_feature_names_out=True)
        try:train_values=pipeline.fit_transform(X_train,y_train);test_values=pipeline.transform(X_test)
        except Exception as exc:raise PreprocessingError("PREPROCESSING_FAILED","Preprocessing could not be fitted or applied.",str(exc)) from exc
        if not np.isfinite(np.asarray(train_values,dtype=float)).all() or not np.isfinite(np.asarray(test_values,dtype=float)).all():raise PreprocessingError("NON_FINITE_OUTPUT","Preprocessing produced non-finite values.")
        if config.task_type=="classification":
            labels=LabelEncoder().fit(y_train);train_labels=labels.transform(y_train)
            try:test_labels=labels.transform(y_test)
            except ValueError as exc:raise PreprocessingError("UNSEEN_TEST_LABEL","Test split contains a target label absent from training.",str(exc)) from exc
        else:
            labels=None;train_labels=np.asarray(y_train,dtype=float);test_labels=np.asarray(y_test,dtype=float)
        transformed_names=[str(name) for name in pipeline.get_feature_names_out()]
        reduced=reduce_features(train_values,test_values,train_labels,transformed_names,config.feature_selection_method,config.feature_count,config.variance_threshold,config.reduction_method,config.pca_components,config.random_seed,config.task_type)
        resampling=apply_resampling(reduced.train,train_labels,config.resampling_method,config.random_seed,config.smote_k_neighbors,config.task_type)
        names=reduced.output_feature_names;run_id=str(uuid.uuid4());artifact_path=self.artifact_dir/f"{run_id}.joblib";artifact_reference=f"preprocessing/{run_id}.joblib"
        bundle={"pipeline":pipeline,"outlier_policy":policy,"label_encoder":labels,"feature_selector":reduced.selector,"dimensionality_reducer":reduced.reducer,"resampling":{"method":resampling.method,"rows_before":resampling.rows_before,"rows_after":resampling.rows_after,"distribution_before":resampling.distribution_before,"distribution_after":resampling.distribution_after},"configuration":config.model_dump(),"task_type":config.task_type,"input_columns":[str(c) for c in X.columns],"output_feature_names":names,"training_features":resampling.features,"training_labels":resampling.labels,"test_features":reduced.test,"test_labels":test_labels,"fitted_on":"training_only"}
        joblib.dump(bundle,artifact_path)
        summary={"task_type":config.task_type,"input_rows":input_rows,"rows_after_duplicates":rows_after_duplicates,"duplicates_removed":duplicates if config.duplicate_mode=="remove" else 0,"train_rows":len(X_train),"test_rows":len(X_test),"train_rows_before_resampling":resampling.rows_before,"train_rows_after_resampling":resampling.rows_after,"resampling_method":resampling.method,"resampling_rows_added":resampling.rows_added,"resampling_rows_removed":resampling.rows_removed,"outliers_removed_from_train":removed,"input_features":X.shape[1],"transformed_features":len(transformed_names),"selected_features":len(reduced.selected_feature_names),"output_features":len(names),"feature_selection_method":config.feature_selection_method,"reduction_method":config.reduction_method,"selected_feature_names":reduced.selected_feature_names,"explained_variance_ratio":reduced.explained_variance_ratio,"explained_variance_total":round(sum(reduced.explained_variance_ratio),8) if reduced.explained_variance_ratio else None,"numerical_features":numerical,"categorical_features":categorical,"output_feature_names":names,"train_class_distribution":self._counts(y_train) if config.task_type=="classification" else {},"train_class_distribution_before_resampling":resampling.distribution_before,"train_class_distribution_after_resampling":resampling.distribution_after,"test_class_distribution":self._counts(y_test) if config.task_type=="classification" else {},"fitted_on":"training_only"}
        created_at=datetime.now(timezone.utc).isoformat();persisted={"id":run_id,"dataset_id":config.dataset_id,"status":"completed","configuration":config.model_dump(),"summary":summary,"artifact_path":artifact_reference,"created_at":created_at}
        try:self.runs.create(persisted)
        except Exception:artifact_path.unlink(missing_ok=True);raise
        return self._response(persisted)
    def get(self,run_id:str)->dict:
        record=self.runs.get(run_id)
        if not record:raise PreprocessingError("PREPROCESSING_RUN_NOT_FOUND","Preprocessing run was not found.",run_id,404)
        return self._response(record)
    def list(self,dataset_id:str|None=None)->list[dict]:return [self._response(record) for record in self.runs.list(dataset_id)]
    @staticmethod
    def _counts(values:pd.Series)->dict[str,int]:return {str(k):int(v) for k,v in values.value_counts().items()}
    @staticmethod
    def _response(record:dict)->dict:return {"id":record["id"],"dataset_id":record["dataset_id"],"status":record["status"],"configuration":record["configuration"],"artifact_path":record["artifact_path"],"created_at":record["created_at"],**record["summary"]}
