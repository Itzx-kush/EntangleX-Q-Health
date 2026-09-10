from datetime import datetime
from typing import Literal
from pydantic import BaseModel,Field
class ModelTrainingConfig(BaseModel):
 preprocessing_run_id:str;model_type:Literal['logistic_regression','svm','random_forest']='logistic_regression';random_seed:int=42;regularization_c:float=Field(default=1,gt=0,le=1000);max_iterations:int=Field(default=1000,ge=100,le=10000);n_estimators:int=Field(default=200,ge=10,le=2000);max_depth:int|None=Field(default=None,ge=1,le=100);class_weight:Literal['none','balanced']='none'
class ModelRun(BaseModel):
 id:str;preprocessing_run_id:str;dataset_id:str;status:str;model_type:str;configuration:ModelTrainingConfig;training_rows:int;feature_count:int;class_distribution:dict[str,int];training_duration_seconds:float;artifact_path:str;created_at:datetime
class ModelRunList(BaseModel):items:list[ModelRun];total:int
