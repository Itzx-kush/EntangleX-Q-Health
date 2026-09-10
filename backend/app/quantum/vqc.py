from datetime import datetime,timezone
from pathlib import Path
from time import perf_counter
import uuid,numpy as np
from scipy.optimize import minimize
from app.core.config import settings
from app.evaluation.metrics import evaluate_binary
from app.quantum.errors import QuantumRuntimeError
from app.quantum.qml_repository import QMLRepository
from app.quantum.encoding import QuantumEncodingService
class VQCService:
 def __init__(self,runs=None,artifact_dir=None):self.runs=runs or QMLRepository();self.artifact_dir=artifact_dir or settings.model_dir/'vqc';self.artifact_dir.mkdir(parents=True,exist_ok=True)
 @staticmethod
 def circuit(x,theta,reps,entanglement):
  q=QuantumEncodingService.circuit(x,entanglement);n=len(x);p=0
  for _ in range(reps):
   for wire in range(n):q.ry(float(theta[p]),wire);p+=1
   if n>1:
    for wire in range(n-1):q.cx(wire,wire+1)
    if entanglement=='ring' and n>2:q.cx(n-1,0)
  return q
 @classmethod
 def probability(cls,x,theta,reps,entanglement):
  from qiskit.quantum_info import Statevector
  return float(Statevector.from_instruction(cls.circuit(x,theta,reps,entanglement)).probabilities([0])[1])
 @staticmethod
 def subset(X,y,limit,seed):
  if len(X)<=limit:return X,y
  rng=np.random.default_rng(seed);chosen=[]
  for value in np.unique(y):
   idx=np.flatnonzero(y==value);take=max(1,round(limit*len(idx)/len(y)));chosen.extend(rng.choice(idx,min(take,len(idx)),replace=False).tolist())
  chosen=np.asarray(chosen[:limit]);return X[chosen],y[chosen]
 def train(self,c):
  e=self.runs.get_encoding(c.encoding_run_id)
  if not e:raise QuantumRuntimeError('ENCODING_RUN_NOT_FOUND','Create a quantum encoding run first.',c.encoding_run_id,404)
  path=settings.model_dir/'quantum_encoding'/Path(e['artifact_path']).name
  if not path.exists():raise QuantumRuntimeError('ENCODING_ARTIFACT_NOT_FOUND','The encoded feature artifact is missing.',str(path),404)
  try:from qiskit.quantum_info import Statevector
  except ImportError as exc:raise QuantumRuntimeError('QISKIT_UNAVAILABLE','Install Qiskit before VQC training.') from exc
  z=np.load(path);X,y=self.subset(z['train_features'],z['train_labels'],c.training_samples,c.seed);Xt,yt=self.subset(z['test_features'],z['test_labels'],c.evaluation_samples,c.seed+1);n=X.shape[1];rng=np.random.default_rng(c.seed);initial=rng.normal(0,.15,n*c.ansatz_reps);history=[]
  def objective(theta):
   p=np.clip(np.asarray([self.probability(x,theta,c.ansatz_reps,e['configuration']['entanglement']) for x in X]),1e-7,1-1e-7);loss=float(-np.mean(y*np.log(p)+(1-y)*np.log(1-p)));history.append(loss);return loss
  started=perf_counter();initial_loss=objective(initial);result=minimize(objective,initial,method='COBYLA',options={'maxiter':c.max_iterations,'rhobeg':.5,'tol':1e-4});duration=round(perf_counter()-started,6);scores=np.asarray([self.probability(x,result.x,c.ansatz_reps,e['configuration']['entanglement']) for x in Xt]);metrics=evaluate_binary(yt,(scores>=.5).astype(int),scores);sample=self.circuit(X[0],result.x,c.ansatz_reps,e['configuration']['entanglement']);i=str(uuid.uuid4());artifact=self.artifact_dir/f'{i}.npz';np.savez_compressed(artifact,parameters=result.x,loss_history=np.asarray(history),configuration=np.asarray([str(c.model_dump())]))
  summary={'training_rows':len(X),'evaluation_rows':len(Xt),'parameter_count':len(result.x),'iterations_completed':int(getattr(result,'nfev',len(history))),'initial_loss':float(initial_loss),'final_loss':float(result.fun),'converged':bool(result.success),'training_duration_seconds':duration,**metrics,'circuit_depth':int(sample.depth()),'circuit_size':int(sample.size()),'operation_counts':{str(k):int(v) for k,v in sample.count_ops().items()},'loss_history':[float(x) for x in history]}
  record={'id':i,'encoding_run_id':c.encoding_run_id,'preprocessing_run_id':e['preprocessing_run_id'],'dataset_id':e['dataset_id'],'status':'completed','configuration':c.model_dump(),'summary':summary,'artifact_path':f'vqc/{i}.npz','created_at':datetime.now(timezone.utc).isoformat()};self.runs.create_vqc(record);return self._response(record)
 def get(self,i):
  r=self.runs.get_vqc(i)
  if not r:raise QuantumRuntimeError('VQC_RUN_NOT_FOUND','VQC run was not found.',i,404)
  return self._response(r)
 @staticmethod
 def _response(r):return{'id':r['id'],'encoding_run_id':r['encoding_run_id'],'preprocessing_run_id':r['preprocessing_run_id'],'dataset_id':r['dataset_id'],'status':r['status'],'configuration':r['configuration'],**r['summary'],'artifact_path':r['artifact_path'],'created_at':r['created_at']}
