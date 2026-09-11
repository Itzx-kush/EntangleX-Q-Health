import importlib.util,tempfile,unittest
from pathlib import Path
import numpy as np
from pydantic import ValidationError
from app.quantum.encoding import QuantumEncodingService
from app.quantum.qml_schemas import EncodingRequest,VQCRequest
class QMLContractTests(unittest.TestCase):
 def test_encoding_and_vqc_limits(self):
  with self.assertRaises(ValidationError):EncodingRequest(preprocessing_run_id='x',qubits=9)
  with self.assertRaises(ValidationError):VQCRequest(encoding_run_id='x',ansatz_reps=5)
 def test_scaler_fits_train_only_and_clips_test(self):
  train=np.asarray([[0.,2.],[10.,4.]]);test=np.asarray([[20.,0.]])
  a,b,low,high=QuantumEncodingService.fit_angle_scaler(train,test)
  self.assertTrue(np.allclose(low,[0,2]));self.assertTrue(np.allclose(high,[10,4]));self.assertTrue(np.allclose(a,[[0,0],[np.pi,np.pi]]));self.assertTrue(np.allclose(b,[[np.pi,0]]))
@unittest.skipUnless(importlib.util.find_spec('qiskit'),'Qiskit not installed')
class QMLExecutionTests(unittest.TestCase):
 def test_probability_changes_with_features_and_parameters(self):
  from app.quantum.vqc import VQCService
  zero=np.zeros(4);theta=np.asarray([.1,.2,.3,.4]);a=VQCService.probability(zero,theta,1,'linear');b=VQCService.probability(np.asarray([1.,.5,.2,.8]),theta,1,'linear');c=VQCService.probability(zero,theta+.4,1,'linear');self.assertFalse(np.isclose(a,b));self.assertFalse(np.isclose(a,c))
if __name__=='__main__':unittest.main()
