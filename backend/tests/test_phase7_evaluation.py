import importlib.util,unittest
import numpy as np
SKLEARN=importlib.util.find_spec('sklearn') is not None
@unittest.skipUnless(SKLEARN,'scikit-learn not installed')
class EvaluationMetricTests(unittest.TestCase):
 def test_binary_metrics_match_confusion_matrix(self):
  from app.evaluation.metrics import evaluate_binary
  r=evaluate_binary(np.array([0,0,1,1]),np.array([0,1,1,1]),np.array([.1,.8,.7,.9]));self.assertEqual((r['true_negative'],r['false_positive'],r['false_negative'],r['true_positive']),(1,1,0,2));self.assertAlmostEqual(r['sensitivity'],1);self.assertAlmostEqual(r['specificity'],.5);self.assertAlmostEqual(r['accuracy'],.75);self.assertIsNotNone(r['roc_auc'])
 def test_undefined_precision_is_zero(self):
  from app.evaluation.metrics import evaluate_binary
  r=evaluate_binary(np.array([0,1]),np.array([0,0]));self.assertEqual(r['precision'],0);self.assertEqual(r['f1'],0)
