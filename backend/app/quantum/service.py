from datetime import datetime,timezone
from importlib.util import find_spec
from time import perf_counter
import json,os,uuid
from app.core.config import settings
from app.quantum.errors import QuantumRuntimeError
from app.quantum.repository import QuantumRunRepository
class QuantumRuntimeService:
 def __init__(self,runs=None,artifact_dir=None):self.runs=runs or QuantumRunRepository();self.artifact_dir=artifact_dir or settings.model_dir/'quantum';self.artifact_dir.mkdir(parents=True,exist_ok=True)
 def status(self):
  qiskit=find_spec('qiskit') is not None;aer=find_spec('qiskit_aer') is not None;ibm=find_spec('qiskit_ibm_runtime') is not None;token=bool(os.getenv('QISKIT_IBM_TOKEN'))
  return{'simulator_available':qiskit and aer,'qiskit_available':qiskit,'ibm_runtime_available':ibm,'ibm_token_configured':token,'real_quantum_enabled':settings.enable_real_quantum,'provider_ready':ibm and token and settings.enable_real_quantum,'default_backend':settings.quantum_backend,'default_qubits':settings.default_qubits,'max_qubits':settings.max_qubits,'max_shots':settings.max_quantum_shots}
 def run_diagnostic(self,c):
  if c.qubits>settings.max_qubits:raise QuantumRuntimeError('QUBIT_LIMIT_EXCEEDED','Requested qubits exceed the configured safety limit.',f'Maximum: {settings.max_qubits}.')
  if c.shots>settings.max_quantum_shots:raise QuantumRuntimeError('SHOT_LIMIT_EXCEEDED','Requested shots exceed the configured safety limit.',f'Maximum: {settings.max_quantum_shots}.')
  if c.backend!='aer_simulator':
   s=self.status()
   if not s['provider_ready']:raise QuantumRuntimeError('IBM_RUNTIME_NOT_READY','IBM Quantum execution is disabled or not configured. Use the simulator or configure the optional provider.')
   raise QuantumRuntimeError('IBM_EXECUTION_DEFERRED','Hardware job submission is intentionally deferred until an explicit backend-selection workflow is available.')
  if not self.status()['simulator_available']:raise QuantumRuntimeError('QUANTUM_SIMULATOR_UNAVAILABLE','Install the Phase 8 Qiskit and Aer dependencies before running diagnostics.')
  from qiskit import QuantumCircuit,transpile
  from qiskit_aer import AerSimulator
  circuit=QuantumCircuit(c.qubits,c.qubits,name='ghz_diagnostic');circuit.h(0)
  for index in range(1,c.qubits):circuit.cx(index-1,index)
  circuit.measure(range(c.qubits),range(c.qubits));backend=AerSimulator(seed_simulator=c.seed);compiled=transpile(circuit,backend,optimization_level=1,seed_transpiler=c.seed);started=perf_counter();result=backend.run(compiled,shots=c.shots,seed_simulator=c.seed).result();duration=round(perf_counter()-started,6);counts={str(k):int(v) for k,v in sorted(result.get_counts().items())};resources={'circuit_name':circuit.name,'circuit_depth':int(compiled.depth()),'circuit_size':int(compiled.size()),'operation_counts':{str(k):int(v) for k,v in compiled.count_ops().items()}};i=str(uuid.uuid4());artifact=self.artifact_dir/f'{i}.json';payload={'run_id':i,'backend':'aer_simulator','execution_mode':'simulator','configuration':c.model_dump(),'resources':resources,'measurement_counts':counts,'execution_duration_seconds':duration};artifact.write_text(json.dumps(payload,indent=2));record={**payload,'id':i,'artifact_path':f'quantum/{i}.json','created_at':datetime.now(timezone.utc).isoformat()};self.runs.create(record);return self._response(record)
 def get(self,i):
  r=self.runs.get(i)
  if not r:raise QuantumRuntimeError('QUANTUM_RUN_NOT_FOUND','Quantum diagnostic run was not found.',i,404)
  return self._response(r)
 def list(self):return[self._response(r) for r in self.runs.list()]
 @staticmethod
 def _response(r):return{'id':r['id'],'backend':r['backend'],'execution_mode':r['execution_mode'],'qubits':r['configuration']['qubits'],'shots':r['configuration']['shots'],'seed':r['configuration']['seed'],**r['resources'],'measurement_counts':r['measurement_counts'],'execution_duration_seconds':r['execution_duration_seconds'],'artifact_path':r['artifact_path'],'created_at':r['created_at']}
