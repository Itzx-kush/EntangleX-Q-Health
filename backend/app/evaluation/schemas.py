from datetime import datetime
from pydantic import BaseModel
class EvaluationRequest(BaseModel):model_run_id:str
class ROCCurvePoint(BaseModel):false_positive_rate:float;true_positive_rate:float;threshold:float|None
class PrecisionRecallPoint(BaseModel):recall:float;precision:float;threshold:float|None
class EvaluationRun(BaseModel):
 id:str;model_run_id:str;preprocessing_run_id:str;dataset_id:str;model_type:str;status:str;test_rows:int;accuracy:float;balanced_accuracy:float;precision:float;recall:float;f1:float;sensitivity:float;specificity:float;roc_auc:float|None;pr_auc:float|None;roc_curve:list[ROCCurvePoint];precision_recall_curve:list[PrecisionRecallPoint];true_negative:int;false_positive:int;false_negative:int;true_positive:int;support_negative:int;support_positive:int;evaluation_duration_seconds:float;artifact_path:str;created_at:datetime
class EvaluationRunList(BaseModel):items:list[EvaluationRun];total:int
