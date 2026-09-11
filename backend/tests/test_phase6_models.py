import importlib.util,tempfile,unittest
from pathlib import Path
import numpy as np
SKLEARN=importlib.util.find_spec("sklearn") is not None
@unittest.skipUnless(SKLEARN,"scikit-learn not installed")
class ModelFactoryTests(unittest.TestCase):
 def test_all_classical_estimators_fit(self):
  from app.ml.factory import build_estimator
  from app.ml.schemas import ModelTrainingConfig
  X=np.array([[i,i%3] for i in range(30)],dtype=float);y=np.array([i%2 for i in range(30)])
  for kind in ("logistic_regression","svm","random_forest"):
   model=build_estimator(ModelTrainingConfig(preprocessing_run_id="test",model_type=kind,n_estimators=20));model.fit(X,y);self.assertEqual(len(model.predict(X)),30)
if __name__=="__main__":unittest.main()
