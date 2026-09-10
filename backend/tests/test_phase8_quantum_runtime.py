import importlib.util,unittest
from pydantic import ValidationError
from app.quantum.schemas import QuantumDiagnosticRequest
class QuantumRuntimeContractTests(unittest.TestCase):
 def test_qubit_and_shot_limits(self):
  with self.assertRaises(ValidationError):QuantumDiagnosticRequest(qubits=9)
  with self.assertRaises(ValidationError):QuantumDiagnosticRequest(shots=8193)
 def test_defaults_are_deterministic_and_simulator_first(self):
  c=QuantumDiagnosticRequest();self.assertEqual(c.backend,'aer_simulator');self.assertEqual(c.seed,42);self.assertEqual(c.qubits,4)
@unittest.skipUnless(importlib.util.find_spec('qiskit') and importlib.util.find_spec('qiskit_aer'),'Qiskit Aer not installed')
class QuantumExecutionTests(unittest.TestCase):
 def test_diagnostic_counts_equal_shots(self):
  import tempfile
  from pathlib import Path
  from app.quantum.service import QuantumRuntimeService
  class Runs:
   def create(self,r):self.value=r
  r=QuantumRuntimeService(runs=Runs(),artifact_dir=Path(tempfile.mkdtemp())).run_diagnostic(QuantumDiagnosticRequest(qubits=2,shots=128,seed=7));self.assertEqual(sum(r['measurement_counts'].values()),128);self.assertGreater(r['circuit_depth'],0)
