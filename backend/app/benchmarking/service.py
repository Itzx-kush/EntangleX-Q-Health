from __future__ import annotations

import math
import statistics
import uuid
from datetime import datetime, timezone
from typing import Any

from app.benchmarking.errors import BenchmarkError
from app.benchmarking.repository import BenchmarkRepository
from app.benchmarking.schemas import BenchmarkCreateRequest, FoldResult
from app.experiments.registry import ExperimentRegistry

RESOURCE_KEYS = {"duration_seconds", "training_seconds", "inference_seconds", "simulator_seconds", "circuit_depth", "circuit_size", "memory_mb", "shots"}

def _summary(values: list[float]) -> dict[str, Any]:
    if not values:return {"n":0,"mean":None,"std":None,"confidence_interval_95":None}
    mean=statistics.fmean(values);std=statistics.stdev(values) if len(values)>1 else None;interval=None if std is None else [mean-1.96*std/math.sqrt(len(values)),mean+1.96*std/math.sqrt(len(values))]
    return {"n":len(values),"mean":mean,"std":std,"confidence_interval_95":interval}

def _binary_metrics(labels:list[int],predictions:list[int],probabilities:list[float]|None,bins:int)->dict[str,float]:
    if len(labels)!=len(predictions) or (probabilities is not None and len(labels)!=len(probabilities)):raise BenchmarkError("PREDICTION_LENGTH_MISMATCH","Labels, predictions and probabilities must have matching lengths.",{},422)
    tp=sum(y==1 and p==1 for y,p in zip(labels,predictions));tn=sum(y==0 and p==0 for y,p in zip(labels,predictions));fp=sum(y==0 and p==1 for y,p in zip(labels,predictions));fn=sum(y==1 and p==0 for y,p in zip(labels,predictions));total=len(labels);sensitivity=tp/(tp+fn) if tp+fn else None;specificity=tn/(tn+fp) if tn+fp else None;precision=tp/(tp+fp) if tp+fp else None;f1=2*precision*sensitivity/(precision+sensitivity) if precision is not None and sensitivity is not None and precision+sensitivity else None;result={"accuracy":(tp+tn)/total if total else 0.0}
    for name,value in (("sensitivity",sensitivity),("specificity",specificity),("precision",precision),("f1",f1)):
        if value is not None:result[name]=value
    if probabilities is not None:
        result["brier_score"]=sum((probability-label)**2 for probability,label in zip(probabilities,labels))/total if total else 0.0;bucket_values=[]
        for index in range(bins):
            lower=index/bins;upper=(index+1)/bins;selected=[(probability,label) for probability,label in zip(probabilities,labels) if lower<=probability<upper or (index==bins-1 and probability==upper)]
            if selected:bucket_values.append((statistics.fmean(pair[0] for pair in selected),len(selected),statistics.fmean(pair[1] for pair in selected)))
        result["ece"]=sum(size/total*abs(confidence-accuracy) for confidence,size,accuracy in bucket_values) if total else 0.0
    return result

class BenchmarkService:
    def __init__(self,repository:BenchmarkRepository|None=None,experiments:ExperimentRegistry|None=None):self.repository=repository or BenchmarkRepository();self.experiments=experiments or ExperimentRegistry()
    def create(self,request:BenchmarkCreateRequest)->dict[str,Any]:
        records=[self.experiments.get(item.experiment_id) for item in request.experiments];signatures={(record["task_type"],record["model_family"],record["modality"]) for record in records}
        if len(signatures)>1:raise BenchmarkError("INCOMPATIBLE_EXPERIMENTS","Benchmark experiments must share task type, model family and modality.",{},409)
        reports=[self._summarize_experiment(item.experiment_id,item.fold_results,request) for item in request.experiments]
        report={"validation_plan":{"stratified":request.stratified,"repeats":request.repeats,"folds":request.folds,"observed_fold_results":sum(len(item.fold_results) for item in request.experiments)},"primary_metric":request.primary_metric,"experiments":reports,"comparison":self._comparison(reports,request.primary_metric),"notes":list(request.notes)+["Metrics and resources are aggregated from supplied recorded folds; no missing values were fabricated.","A single benchmark does not establish clinical validity or quantum advantage."]}
        record={"id":str(uuid.uuid4()),"primary_metric":request.primary_metric,"experiment_ids":[item.experiment_id for item in request.experiments],"request":request.model_dump(mode="json"),"report":report,"created_at":datetime.now(timezone.utc).isoformat()};self.repository.create(record);return {**record,"report":report}
    def get(self,benchmark_id:str)->dict[str,Any]:
        record=self.repository.get(benchmark_id)
        if not record:raise BenchmarkError("BENCHMARK_NOT_FOUND","The benchmark report was not found.",{"benchmark_id":benchmark_id},404)
        return record
    def list(self)->list[dict[str,Any]]:return self.repository.list()
    def _summarize_experiment(self,experiment_id:str,folds:list[FoldResult],request:BenchmarkCreateRequest)->dict[str,Any]:
        metric_values:dict[str,list[float]]={};train_values:dict[str,list[float]]={};gaps:dict[str,list[float]]={};resource_values:dict[str,list[float]]={};warnings=[]
        for fold in folds:
            validation=dict(fold.validation_metrics)
            if fold.labels is not None or fold.predictions is not None:
                if fold.labels is None or fold.predictions is None:raise BenchmarkError("PREDICTIONS_REQUIRED","Labels and predictions must be supplied together.",{"experiment_id":experiment_id},422)
                validation.update(_binary_metrics(fold.labels,fold.predictions,fold.probabilities,request.calibration_bins))
            for name,value in validation.items():metric_values.setdefault(name,[]).append(float(value))
            for name,value in fold.train_metrics.items():
                train_values.setdefault(name,[]).append(float(value))
                if name in validation:gaps.setdefault(name,[]).append(float(value)-float(validation[name]))
            for name,value in fold.resource_measurements.items():
                if name in RESOURCE_KEYS:resource_values.setdefault(name,[]).append(float(value))
            if fold.duration_seconds is not None:resource_values.setdefault("duration_seconds",[]).append(float(fold.duration_seconds))
            if fold.probabilities is None:warnings.append(f"{fold.repeat}:{fold.fold} has no probabilities; calibration metrics are unavailable for that fold.")
        return {"experiment_id":experiment_id,"integrity":self.experiments.get(experiment_id)["integrity"],"metrics":{name:_summary(values) for name,values in sorted(metric_values.items())},"generalization_gaps":{name:_summary(values) for name,values in sorted(gaps.items())},"resources":{name:_summary(values) for name,values in sorted(resource_values.items())},"fold_count":len(folds),"warnings":list(dict.fromkeys(warnings))}
    @staticmethod
    def _comparison(reports:list[dict[str,Any]],primary_metric:str)->dict[str,Any]:
        values=[(item["experiment_id"],item["metrics"].get(primary_metric,{}).get("mean"),item["metrics"].get(primary_metric,{}).get("confidence_interval_95")) for item in reports];conclusion="inconclusive"
        if len(values)==2 and all(value[1] is not None for value in values):
            first,second=values;first_interval,second_interval=first[2],second[2]
            if first_interval and second_interval and first_interval[1]<second_interval[0]:conclusion="worse"
            elif first_interval and second_interval and second_interval[1]<first_interval[0]:conclusion="better"
            else:conclusion="comparable"
        return {"primary_metric":primary_metric,"conclusion":conclusion,"comparisons":[{"experiment_id":experiment_id,"mean":mean,"confidence_interval_95":interval} for experiment_id,mean,interval in values],"note":"Conclusion is a descriptive interval comparison, not a statistical claim of superiority."}
