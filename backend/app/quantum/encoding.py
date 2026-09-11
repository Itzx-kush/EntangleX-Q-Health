from datetime import datetime,timezone
from pathlib import Path
import uuid,numpy as np
from app.core.config import settings
from app.preprocessing.repository import PreprocessingRepository
from app.quantum.errors import QuantumRuntimeError
from app.quantum.qml_repository import QMLRepository

class QuantumEncodingService:
 def __init__(self,preprocessing=None,runs=None,artifact_dir=None):self.preprocessing=preprocessing or PreprocessingRepository();self.runs=runs or QMLRepository();self.artifact_dir=artifact_dir or settings.model_dir/'quantum_encoding';self.artifact_dir.mkdir(parents=True,exist_ok=True)
 @staticmethod
 def fit_angle_scaler(train,test):
  low=np.min(train,axis=0);high=np.max(train,axis=0);span=np.where(high-low==0,1.,high-low)
  return np.clip((train-low)/span*np.pi,0.,np.pi),np.clip((test-low)/span*np.pi,0.,np.pi),low,high
 @staticmethod
 def circuit(values,entanglement):
  from qiskit import QuantumCircuit
  q=QuantumCircuit(len(values),name='biomedical_angle_encoding')
  for i,v in enumerate(values):q.ry(float(v),i)
  if len(values)>1:
   for i in range(len(values)-1):q.cx(i,i+1)
   if entanglement=='ring' and len(values)>2:q.cx(len(values)-1,0)
  return q
 def create(self,c):
  r=self.preprocessing.get(c.preprocessing_run_id)
  if not r:raise QuantumRuntimeError('PREPROCESSING_RUN_NOT_FOUND','Preprocessing run was not found.',c.preprocessing_run_id,404)
  path=settings.model_dir/'preprocessing'/Path(r['artifact_path']).name
  if not path.exists():raise QuantumRuntimeError('PREPROCESSING_ARTIFACT_NOT_FOUND','The preprocessing artifact is missing. Rerun preprocessing.',str(path),404)
  import joblib
  b=joblib.load(path);train=np.asarray(b['training_features'],dtype=float);test=np.asarray(b['test_features'],dtype=float)
  if train.ndim!=2 or train.shape[1]<c.qubits:raise QuantumRuntimeError('INSUFFICIENT_FEATURES','The preprocessing output has fewer features than the requested qubits.',f'Available: {train.shape[1]}; requested: {c.qubits}.')
  names=list(b.get('output_feature_names',[]))[:c.qubits];train=train[:,:c.qubits];test=test[:,:c.qubits];encoded_train,encoded_test,low,high=self.fit_angle_scaler(train,test)
  try:
   from qiskit import transpile
   from qiskit_aer import AerSimulator
   compiled=transpile(self.circuit(encoded_train[0],c.entanglement),AerSimulator(),optimization_level=1,seed_transpiler=c.seed)
  except ImportError as exc:raise QuantumRuntimeError('QUANTUM_SIMULATOR_UNAVAILABLE','Install Qiskit and Qiskit Aer before encoding.') from exc
  i=str(uuid.uuid4());artifact=self.artifact_dir/f'{i}.npz';np.savez_compressed(artifact,train_features=encoded_train,test_features=encoded_test,train_labels=np.asarray(b['training_labels']),test_labels=np.asarray(b['test_labels']),feature_min=low,feature_max=high)
  task_type=str(b.get('task_type',b.get('configuration',{}).get('task_type','classification')))
  summary={'task_type':task_type,'feature_names':names,'train_rows':len(train),'test_rows':len(test),'angle_min':float(encoded_train.min()),'angle_max':float(encoded_train.max()),'circuit_depth':int(compiled.depth()),'circuit_size':int(compiled.size()),'operation_counts':{str(k):int(v) for k,v in compiled.count_ops().items()}}
  record={'id':i,'preprocessing_run_id':c.preprocessing_run_id,'dataset_id':r['dataset_id'],'configuration':c.model_dump(),'summary':summary,'artifact_path':f'quantum_encoding/{i}.npz','created_at':datetime.now(timezone.utc).isoformat()};self.runs.create_encoding(record);return self._response(record)
 def get(self,i):
  r=self.runs.get_encoding(i)
  if not r:raise QuantumRuntimeError('ENCODING_RUN_NOT_FOUND','Quantum encoding run was not found.',i,404)
  return self._response(r)
 @staticmethod
 def _response(r):return{'id':r['id'],'preprocessing_run_id':r['preprocessing_run_id'],'dataset_id':r['dataset_id'],**r['configuration'],**r['summary'],'task_type':r['summary'].get('task_type','classification'),'artifact_path':r['artifact_path'],'created_at':r['created_at']}
