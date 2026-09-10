from datetime import datetime
from typing import Literal
from pydantic import BaseModel,Field
class EncodingRequest(BaseModel):
 preprocessing_run_id:str;encoding:Literal['angle']='angle';qubits:int=Field(default=4,ge=1,le=8);entanglement:Literal['linear','ring']='linear';seed:int=42
class EncodingRun(BaseModel):
 id:str;preprocessing_run_id:str;dataset_id:str;encoding:str;qubits:int;entanglement:str;seed:int;feature_names:list[str];train_rows:int;test_rows:int;angle_min:float;angle_max:float;circuit_depth:int;circuit_size:int;operation_counts:dict[str,int];artifact_path:str;created_at:datetime
class VQCRequest(BaseModel):
 encoding_run_id:str;ansatz_reps:int=Field(default=2,ge=1,le=4);optimizer:Literal['cobyla']='cobyla';max_iterations:int=Field(default=25,ge=1,le=200);training_samples:int=Field(default=32,ge=4,le=128);evaluation_samples:int=Field(default=128,ge=4,le=512);seed:int=42
class VQCRun(BaseModel):
 id:str;encoding_run_id:str;preprocessing_run_id:str;dataset_id:str;status:str;configuration:dict;training_rows:int;evaluation_rows:int;parameter_count:int;iterations_completed:int;initial_loss:float;final_loss:float;converged:bool;training_duration_seconds:float;accuracy:float;balanced_accuracy:float;precision:float;recall:float;f1:float;sensitivity:float;specificity:float;roc_auc:float|None;true_negative:int;false_positive:int;false_negative:int;true_positive:int;circuit_depth:int;circuit_size:int;operation_counts:dict[str,int];loss_history:list[float];artifact_path:str;created_at:datetime
