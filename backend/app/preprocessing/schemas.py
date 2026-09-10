from __future__ import annotations
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class PreprocessingConfig(BaseModel):
    dataset_id: str
    test_size: float = Field(default=0.2, gt=0.05, lt=0.5)
    random_seed: int = 42
    duplicate_mode: Literal["keep","remove"] = "remove"
    numerical_missing: Literal["median","mean"] = "median"
    categorical_missing: Literal["most_frequent"] = "most_frequent"
    categorical_encoding: Literal["one_hot","ordinal"] = "one_hot"
    scaling: Literal["standard","minmax"] = "standard"
    outlier_method: Literal["iqr","zscore"] | None = None
    outlier_mode: Literal["keep","clip","remove"] = "keep"
    outlier_threshold: float = Field(default=1.5, gt=0)
    resampling_method: Literal["none","random_over","random_under","smote"] = "none"
    smote_k_neighbors: int = Field(default=5, ge=1, le=20)
    @model_validator(mode="after")
    def validate_outliers(self):
        if self.outlier_mode != "keep" and self.outlier_method is None:raise ValueError("outlier_method is required when outlier_mode is clip or remove")
        return self

class PreprocessingRun(BaseModel):
    id:str;dataset_id:str;status:str;configuration:PreprocessingConfig
    input_rows:int;rows_after_duplicates:int;duplicates_removed:int;train_rows:int;test_rows:int
    train_rows_before_resampling:int;train_rows_after_resampling:int;resampling_method:str;resampling_rows_added:int;resampling_rows_removed:int
    outliers_removed_from_train:int;input_features:int;output_features:int
    numerical_features:list[str];categorical_features:list[str];output_feature_names:list[str]
    train_class_distribution:dict[str,int];train_class_distribution_before_resampling:dict[str,int];train_class_distribution_after_resampling:dict[str,int];test_class_distribution:dict[str,int]
    artifact_path:str;fitted_on:str;created_at:datetime

class PreprocessingRunList(BaseModel):
    items:list[PreprocessingRun];total:int
