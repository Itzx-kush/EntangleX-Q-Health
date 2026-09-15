from __future__ import annotations
import hashlib, json, os, uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any
import numpy as np
from app.controlled_experiments.repository import ControlledExperimentRepository
from app.controlled_experiments.schemas import ControlledExperimentRequest
from app.core.config import settings
from app.data.repository import DatasetRepository
from app.evaluation.schemas import EvaluationRequest
from app.evaluation.service import EvaluationService
from app.ml.schemas import ModelTrainingConfig
from app.ml.service import ModelTrainingService
from app.preprocessing.repository import PreprocessingRepository
from app.quantum.encoding import QuantumEncodingService
from app.quantum.qml_schemas import EncodingRequest, QNNRequest, QSVMRequest, VQCRequest
from app.quantum.qnn import QNNService
from app.quantum.qsvm import QSVMService
from app.quantum.vqc import VQCService
from app.services.capabilities import runtime_capabilities
from app.storage.database import check_database

QUANTUM={"vqc","qsvm","qnn"}; CLASSICAL={"logistic_regression","svm","random_forest"}
def now(): return datetime.now(timezone.utc).isoformat()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(",",":"),default=str)
def digest_file(path: Path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):h.update(chunk)
    return h.hexdigest()

class ControlledExperimentService:
    def __init__(self, repository=None, executor=None):
        self.repository=repository or ControlledExperimentRepository(); self.preprocessing=PreprocessingRepository(); self.datasets=DatasetRepository(); self.encoding=QuantumEncodingService(); self.classical=ModelTrainingService(); self.evaluation=EvaluationService(); self.vqc=VQCService(); self.qsvm=QSVMService(); self.qnn=QNNService(); self.executor=executor or ThreadPoolExecutor(max_workers=max(1,int(os.getenv("MAX_CONCURRENT_EXPERIMENT_MODELS","2"))),thread_name_prefix="entanglex-model")
    def create(self, request: ControlledExperimentRequest):
        active=sum(1 for item in self.repository.list_experiments() if item["status"] in {"queued","running"})
        if active>=int(os.getenv("MAX_QUEUED_EXPERIMENTS","8")):raise ValueError("The bounded experiment queue is full.")
        prep=self.preprocessing.get(request.preprocessing_run_id)
        if not prep:raise ValueError("The preprocessing run does not exist.")
        dataset=self.datasets.get(prep["dataset_id"])
        if not dataset:raise ValueError("The preprocessing dataset does not exist.")
        task=(prep.get("configuration") or {}).get("task_type","classification")
        if task=="regression" and set(request.models)&{"vqc","qsvm"}:raise ValueError("VQC and QSVM require a classification experiment; QNN supports the existing regression path.")
        quantum_models=set(request.models)&QUANTUM; encoding_run=None
        if quantum_models:
            dimensions=int(request.quantum.get("qubits",4))
            if dimensions>int((prep.get("summary") or {}).get("output_features",0)):raise ValueError("Quantum feature dimensions exceed the shared preprocessing output.")
            encoding_run=self.encoding.create(EncodingRequest(preprocessing_run_id=request.preprocessing_run_id,encoding="angle",qubits=dimensions,entanglement=request.quantum.get("entanglement","linear"),seed=int(request.quantum.get("seed",42))))
        shared={"dataset_id":prep["dataset_id"],"dataset_sha256":dataset.get("sha256"),"target":dataset.get("target_column"),"target_metadata":dataset.get("target"),"preprocessing_run_id":request.preprocessing_run_id,"preprocessing_configuration":prep.get("configuration"),"split_seed":(prep.get("configuration") or {}).get("random_seed"),"test_size":(prep.get("configuration") or {}).get("test_size"),"selected_features":(prep.get("summary") or {}).get("selected_feature_names"),"output_features":(prep.get("summary") or {}).get("output_feature_names"),"encoding_run_id":getattr(encoding_run,"id",None),"quantum_configuration":request.quantum if quantum_models else None}
        fingerprint=hashlib.sha256(canonical(shared).encode()).hexdigest(); experiment_id=str(uuid.uuid4()); created=now()
        configuration={"request":request.model_dump(),"shared_conditions":shared,"comparison_policy":{"metric":request.comparison_metric,"scope":"same held-out partition","cv_status":"not_executed_by_current_runner","note":"CV is never inferred from held-out results."}}
        warnings=["Research/model output only; not a diagnosis or treatment recommendation.","Quantum execution uses exact local statevector simulation in the existing model services; it is not physical hardware.","The controlled runner compares the persisted shared held-out partition. Cross-validation is reported as unavailable until fold-safe execution is implemented."]
        self.repository.create_experiment({"id":experiment_id,"name":request.name,"preprocessing_run_id":request.preprocessing_run_id,"encoding_run_id":getattr(encoding_run,"id",None),"comparison_fingerprint":fingerprint,"status":"queued","configuration":configuration,"warnings":warnings,"parent_experiment_id":request.parent_experiment_id,"created_at":created})
        jobs=[]
        for model in request.models:
            job={"id":str(uuid.uuid4()),"experiment_id":experiment_id,"model_type":model,"status":"queued","stage":"queued","checkpoint":0,"total_checkpoints":4 if model in CLASSICAL else 3,"created_at":created}; self.repository.create_job(job); jobs.append(job)
        self.repository.update_experiment(experiment_id,status="running",started_at=now())
        for job in jobs:self.executor.submit(self._run_model,experiment_id,job["id"],job["model_type"],request)
        return self.get(experiment_id)
    def _run_model(self, experiment_id, job_id, model, request):
        started=perf_counter(); self.repository.update_job(job_id,status="running",stage="building_model",checkpoint=1,started_at=now())
        try:
            if self.repository.get_job(job_id)["cancel_requested"]:return self._cancel_job(job_id)
            parameters=request.model_parameters.get(model,{})
            if model in CLASSICAL:
                self.repository.update_job(job_id,stage="training",checkpoint=2)
                allowed={k:v for k,v in parameters.items() if k in ModelTrainingConfig.model_fields and k not in {"preprocessing_run_id","model_type"}}
                trained=self.classical.train(ModelTrainingConfig(preprocessing_run_id=request.preprocessing_run_id,model_type=model,**allowed))
                self.repository.update_job(job_id,stage="evaluating_held_out_partition",checkpoint=3)
                measured=self.evaluation.run(EvaluationRequest(model_run_id=trained["id"]))
                result={"run_id":trained["id"],"evaluation_id":measured["id"],"metrics":{key:value for key,value in measured.items() if key in {"accuracy","balanced_accuracy","precision","recall","f1","sensitivity","specificity","roc_auc","true_negative","false_positive","false_negative","true_positive","evaluation_duration_seconds"}},"training_duration_seconds":trained["training_duration_seconds"],"artifact_path":trained["artifact_path"],"execution":{"family":"classical","mode":"local_cpu"}}
            else:
                self.repository.update_job(job_id,stage="training_and_executing_exact_statevector",checkpoint=2)
                encoding_id=self.repository.get_experiment(experiment_id)["encoding_run_id"]
                if model=="vqc": cls,service=VQCRequest,self.vqc
                elif model=="qsvm": cls,service=QSVMRequest,self.qsvm
                else: cls,service=QNNRequest,self.qnn
                allowed={k:v for k,v in parameters.items() if k in cls.model_fields and k!="encoding_run_id"}
                if "task_type" in cls.model_fields:allowed.setdefault("task_type",(self.preprocessing.get(request.preprocessing_run_id).get("configuration") or {}).get("task_type","classification"))
                trained=service.train(cls(encoding_run_id=encoding_id,**allowed)); raw=trained.model_dump(mode="json") if hasattr(trained,"model_dump") else trained
                metrics=raw.get("metrics") or {key:raw.get(key) for key in ("accuracy","balanced_accuracy","precision","recall","f1","sensitivity","specificity","roc_auc","true_negative","false_positive","false_negative","true_positive") if key in raw}
                result={"run_id":raw["id"],"metrics":metrics,"training_duration_seconds":raw.get("training_duration_seconds"),"artifact_path":raw["artifact_path"],"execution":{"family":"hybrid_quantum","mode":"exact_local_statevector","backend":"qiskit.quantum_info.Statevector","shots":None,"noise_model":None,"hardware":False},"circuit":self._circuit_description(model,raw,encoding_id)}
            self.repository.update_job(job_id,stage="verifying_artifact",checkpoint=self.repository.get_job(job_id)["total_checkpoints"])
            path=settings.model_dir/Path(result["artifact_path"])
            result["artifact_integrity"]={"path":result["artifact_path"],"sha256":digest_file(path),"size_bytes":path.stat().st_size,"verified":True} if path.is_file() else {"path":result["artifact_path"],"verified":False}
            result["elapsed_seconds"]=round(perf_counter()-started,6)
            self.repository.update_job(job_id,status="succeeded",stage="completed",result_json=result,finished_at=now())
        except Exception as exc:
            self.repository.update_job(job_id,status="failed",stage="failed",error_json={"code":getattr(exc,"code",type(exc).__name__),"message":str(exc),"details":getattr(exc,"details",None)},finished_at=now())
        self._refresh_experiment(experiment_id)
    def _circuit_description(self, model, run, encoding_id):
        encoding=self.encoding.runs.get_encoding(encoding_id); encoded=np.load(settings.model_dir/"quantum_encoding"/Path(encoding["artifact_path"]).name); features=np.asarray(encoded["test_features"])[0]; entanglement=encoding["configuration"]["entanglement"]
        if model in {"vqc","qnn"}:
            artifact=np.load(settings.model_dir/model/Path(run["artifact_path"]).name); params=np.asarray(artifact["parameters"]); reps=int(run["configuration"].get("ansatz_reps",1)); quantum=params[:len(features)*reps]; circuit=VQCService.circuit(features,quantum,reps,entanglement); ansatz="repeated RY + CX"
        else:circuit=QuantumEncodingService.circuit(features,entanglement); ansatz="fidelity feature map"
        return {"description_only":True,"execution_evidence":"Metrics were produced by the model service; this diagram is reconstructed from the persisted run configuration and parameters.","model_type":model,"qubits":circuit.num_qubits,"parameters":int(run.get("parameter_count",0)),"feature_map":"RY angle encoding","ansatz":ansatz,"entanglement":entanglement,"depth":int(circuit.depth()),"size":int(circuit.size()),"gate_counts":{str(k):int(v) for k,v in circuit.count_ops().items()},"diagram":str(circuit.draw(output="text"))}
    def _cancel_job(self, job_id):self.repository.update_job(job_id,status="cancelled",stage="cancelled_before_execution",finished_at=now())
    def cancel(self, experiment_id):
        if not self.repository.get_experiment(experiment_id):raise KeyError("Experiment not found")
        for job in self.repository.jobs(experiment_id):
            if job["status"]=="queued":self._cancel_job(job["id"])
            elif job["status"]=="running":self.repository.update_job(job["id"],status="cancel_requested",stage="cancellation_requested",cancel_requested=True)
        self._refresh_experiment(experiment_id); return self.get(experiment_id)
    def rerun(self, experiment_id):
        source=self.repository.get_experiment(experiment_id)
        if not source:raise KeyError("Experiment not found")
        payload=dict(source["configuration"]["request"]); payload["name"]=f"Rerun of {source['name']}"; payload["parent_experiment_id"]=experiment_id; return self.create(ControlledExperimentRequest(**payload))
    def _refresh_experiment(self, experiment_id):
        jobs=self.repository.jobs(experiment_id); statuses={job["status"] for job in jobs}
        if statuses<={"succeeded"}:status="succeeded"
        elif statuses<={"failed","cancelled","interrupted"}:status="failed" if "failed" in statuses else "cancelled"
        elif statuses&{"queued","running","cancel_requested"}:status="running"
        else:status="partial"
        values={"status":status}
        if status in {"succeeded","failed","cancelled","partial"}:values["finished_at"]=now()
        self.repository.update_experiment(experiment_id,**values)
    def get(self, experiment_id):
        experiment=self.repository.get_experiment(experiment_id)
        if not experiment:raise KeyError("Experiment not found")
        jobs=self.repository.jobs(experiment_id); experiment["jobs"]=jobs; experiment["summary"]={"selected":len(jobs),"succeeded":sum(j["status"]=="succeeded" for j in jobs),"failed":sum(j["status"]=="failed" for j in jobs),"cancelled":sum(j["status"]=="cancelled" for j in jobs)}; return experiment
    def list(self):return [self.get(item["id"]) for item in self.repository.list_experiments()]
    def diagnostics(self):
        capabilities=runtime_capabilities(); db_ok,db_error=check_database(); smoke={"status":"unavailable","verified":False,"details":None}
        if capabilities["packages"]["qiskit"]["available"] and capabilities["packages"]["qiskit_aer"]["available"]:
            try:
                from qiskit import QuantumCircuit,transpile
                from qiskit_aer import AerSimulator
                circuit=QuantumCircuit(1,1); circuit.h(0); circuit.measure(0,0); counts=AerSimulator().run(transpile(circuit,AerSimulator()),shots=16,seed_simulator=42).result().get_counts(); smoke={"status":"verified","verified":sum(counts.values())==16,"details":{"shots":16,"observed_states":sorted(counts)}}
            except Exception as exc:smoke={"status":"failed","verified":False,"details":f"{type(exc).__name__}: {exc}"}
        storage={str(path):path.exists() and os.access(path,os.W_OK) for path in (settings.upload_dir,settings.model_dir,settings.experiment_dir)}
        return {"python":capabilities["python"],"packages":capabilities["packages"],"database":{"available":db_ok,"error":db_error},"storage":storage,"quantum":{"availability":"available" if capabilities["packages"]["qiskit"]["available"] else "unavailable","execution_mode":"local_quantum_simulation","smoke_test":smoke,"hardware_verified":False}}
