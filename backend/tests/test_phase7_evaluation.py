import importlib.util,unittest
import numpy as np
SKLEARN=importlib.util.find_spec('sklearn') is not None
@unittest.skipUnless(SKLEARN,'scikit-learn not installed')
class EvaluationMetricTests(unittest.TestCase):
 def test_binary_metrics_match_confusion_matrix(self):
  from app.evaluation.metrics import evaluate_binary
  result=evaluate_binary(np.array([0,0,1,1]),np.array([0,1,1,1]),np.array([.1,.8,.7,.9]));self.assertEqual((result['true_negative'],result['false_positive'],result['false_negative'],result['true_positive']),(1,1,0,2));self.assertAlmostEqual(result['sensitivity'],1);self.assertAlmostEqual(result['specificity'],.5);self.assertAlmostEqual(result['accuracy'],.75);self.assertIsNotNone(result['roc_auc'])
 def test_undefined_precision_is_zero(self):
  from app.evaluation.metrics import evaluate_binary
  result=evaluate_binary(np.array([0,1]),np.array([0,0]));self.assertEqual(result['precision'],0);self.assertEqual(result['f1'],0)
if __name__=='__main__':unittest.main()
